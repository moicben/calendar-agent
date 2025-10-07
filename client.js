import { spawn } from 'child_process';
import readline from 'readline';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class BrowserUseClient {
  constructor(options = {}) {
    this.python = options.python || process.env.BROWSERUSE_PYTHON || 'python3';
    this.script = options.script || join(__dirname, 'agent.py');
    this.env = {
      ...process.env,
      BROWSERUSE_HEADLESS: String(options.headless ?? true),
      BROWSERUSE_MAX_STEPS: String(options.maxSteps ?? 20),
      BROWSERUSE_MODEL: options.model || process.env.BROWSERUSE_MODEL || '',
      BROWSERUSE_PROXY: options.proxy || process.env.BROWSERUSE_PROXY || '',
      BROWSERUSE_TIMEOUT_MS: String(options.timeoutMs ?? 120000)
    };
    this.child = null;
    this.rl = null;
    this.reqId = 0;
    this.pending = new Map();
    this.closed = false;
  }

  async start() {
    if (this.child) return;
    this.child = spawn(this.python, ['-u', this.script], { env: this.env });
    this.rl = readline.createInterface({ input: this.child.stdout });
    this.rl.on('line', (line) => {
      try {
        const msg = JSON.parse(line);
        const { id, ok, result, error } = msg || {};
        if (this.pending.has(id)) {
          const { resolve, reject } = this.pending.get(id);
          this.pending.delete(id);
          if (ok) resolve(result);
          else reject(new Error(error || 'agent_error'));
        }
      } catch {
        // ignore non-JSON lines
      }
    });
    this.child.stderr.on('data', (d) => {
      const s = String(d || '').trim();
      if (s) console.error('[BrowserUse][py]:', s);
    });
    this.child.on('exit', (code) => {
      this.closed = true;
      for (const { reject } of this.pending.values()) {
        reject(new Error(`agent_exit_${code}`));
      }
      this.pending.clear();
    });
    await this._req('ping', {});
  }

  async stop() {
    if (!this.child || this.closed) return;
    try { await this._req('close', {}); } catch {}
    try { this.child.kill('SIGTERM'); } catch {}
    this.child = null;
    if (this.rl) { this.rl.close(); this.rl = null; }
  }

  _req(type, params) {
    if (!this.child || !this.child.stdin.writable) {
      return Promise.reject(new Error('agent_not_running'));
    }
    const id = ++this.reqId;
    const payload = JSON.stringify({ id, type, params }) + '\n';
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.child.stdin.write(payload);
      const t = setTimeout(() => {
        if (this.pending.has(id)) {
          this.pending.delete(id);
          reject(new Error('agent_timeout'));
        }
      }, Number(this.env.BROWSERUSE_TIMEOUT_MS) || 120000);
      const entry = this.pending.get(id);
      if (entry) {
        this.pending.set(id, {
          resolve: (r) => { clearTimeout(t); resolve(r); },
          reject: (e) => { clearTimeout(t); reject(e); }
        });
      }
    });
  }

  goto(url) { return this._req('goto', { url }); }
  click(params) { return this._req('click', params); }
  type(params) { return this._req('type', params); }
  content() { return this._req('content', {}); }
  screenshot(params = {}) { return this._req('screenshot', params); }
  open() { return this._req('open', {}); }
  runGoal(goal, startUrl = null, options = {}) {
    return this._req('run_goal', { goal, startUrl, maxSteps: options.maxSteps });
  }
}



