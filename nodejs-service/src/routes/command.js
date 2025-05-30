const express = require('express');
const { exec, execSync, spawn } = require('child_process');
const { promisify } = require('util');
const path = require('path');
const fs = require('fs');
const logger = require('../utils/logger');

const router = express.Router();
const execAsync = promisify(exec);

// セキュリティ設定
const ALLOWED_COMMANDS = [
  'ls', 'pwd', 'whoami', 'date', 'echo', 'cat', 'head', 'tail', 'grep',
  'find', 'wc', 'sort', 'uniq', 'cut', 'awk', 'sed', 'ps', 'top',
  'df', 'du', 'free', 'uptime', 'uname', 'which', 'whereis',
  'python', 'python3', 'node', 'npm', 'pip', 'pip3',
  'git', 'curl', 'wget', 'ping', 'traceroute', 'nslookup',
  'scrapy', 'celery', 'redis-cli', 'sqlite3',
  'crontab', 'cron', 'service', 'systemctl'
];

const BLOCKED_PATTERNS = [
  /rm\s+-rf/i,
  /sudo/i,
  /su\s/i,
  /passwd/i,
  /chmod\s+777/i,
  />/,  // リダイレクト
  /\|/,  // パイプ
  /;/,   // コマンド連結
  /&&/,  // AND演算子
  /\|\|/, // OR演算子
  /`/,   // バッククォート
  /\$\(/  // コマンド置換
];

// コマンドのセキュリティチェック
function isCommandSafe(command) {
  // 空のコマンドをチェック
  if (!command || command.trim().length === 0) {
    return { safe: false, reason: 'Empty command' };
  }

  // 危険なパターンをチェック
  for (const pattern of BLOCKED_PATTERNS) {
    if (pattern.test(command)) {
      return { safe: false, reason: `Blocked pattern detected: ${pattern}` };
    }
  }

  // 許可されたコマンドかチェック
  const firstCommand = command.trim().split(' ')[0];
  if (!ALLOWED_COMMANDS.includes(firstCommand)) {
    return { safe: false, reason: `Command not allowed: ${firstCommand}` };
  }

  return { safe: true };
}

// 作業ディレクトリの検証
function isWorkingDirectorySafe(workingDir) {
  if (!workingDir) return true;

  const resolvedPath = path.resolve(workingDir);
  const allowedPaths = [
    '/tmp',
    '/home',
    process.cwd(),
    '/var/tmp',
    '/home/igtmtakan/workplace/python/scrapyUI',
    '/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects',
    '/home/igtmtakan/workplace/python/scrapyUI/backend'
  ];

  return allowedPaths.some(allowedPath =>
    resolvedPath.startsWith(path.resolve(allowedPath))
  );
}

// Python環境の設定
function getPythonEnvironment(workingDir = null) {
  const pythonPath = '/home/igtmtakan/.pyenv/versions/3.13.2/bin';
  const currentPath = process.env.PATH || '';

  let pythonPaths = ['/home/igtmtakan/workplace/python/scrapyUI/backend'];

  const env = {
    ...process.env,
    PATH: `${pythonPath}:${currentPath}`,
    PYENV_VERSION: '3.13.2',
    // ロケール設定
    LC_ALL: 'C.UTF-8',
    LANG: 'C.UTF-8'
  };

  // Scrapyプロジェクト内でのみSCRAPY_SETTINGS_MODULEとPYTHONPATHを設定
  if (workingDir && workingDir.includes('scrapy_projects')) {
    // プロジェクト名を取得
    const projectMatch = workingDir.match(/scrapy_projects\/([^\/]+)/);
    if (projectMatch) {
      const projectName = projectMatch[1];
      env.SCRAPY_SETTINGS_MODULE = `${projectName}.settings`;

      // プロジェクトディレクトリとその親ディレクトリをPYTHONPATHに追加
      const projectDir = `/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects/${projectName}`;
      const scrapyProjectsDir = '/home/igtmtakan/workplace/python/scrapyUI/scrapy_projects';
      pythonPaths.unshift(projectDir);
      pythonPaths.unshift(scrapyProjectsDir);
    }
  }

  env.PYTHONPATH = pythonPaths.join(':');
  return env;
}

// コマンドの完全パスを取得
function getCommandPath(command) {
  if (command === 'scrapy') {
    return '/home/igtmtakan/.pyenv/versions/3.13.2/bin/scrapy';
  }
  if (command === 'python' || command === 'python3') {
    return '/home/igtmtakan/.pyenv/versions/3.13.2/bin/python';
  }
  if (command === 'pip' || command === 'pip3') {
    return '/home/igtmtakan/.pyenv/versions/3.13.2/bin/pip';
  }
  return command;
}

/**
 * @swagger
 * /api/command/exec:
 *   post:
 *     summary: Execute a shell command
 *     description: Execute a shell command with security restrictions
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - command
 *             properties:
 *               command:
 *                 type: string
 *                 description: Command to execute
 *                 example: "ls -la"
 *               workingDir:
 *                 type: string
 *                 description: Working directory (optional)
 *                 example: "/tmp"
 *               timeout:
 *                 type: integer
 *                 description: Timeout in milliseconds (default: 30000)
 *                 example: 10000
 *               encoding:
 *                 type: string
 *                 description: Output encoding (default: utf8)
 *                 example: "utf8"
 *     responses:
 *       200:
 *         description: Command executed successfully
 *       400:
 *         description: Invalid request or unsafe command
 *       500:
 *         description: Command execution failed
 */
router.post('/exec', async (req, res) => {
  const startTime = Date.now();

  try {
    const {
      command,
      workingDir = process.cwd(),
      timeout,
      encoding = 'utf8'
    } = req.body;

    // Set timeout based on command type
    const isScrapyCrawl = command.includes('scrapy crawl');
    const defaultTimeout = isScrapyCrawl ? 300000 : 30000; // 5 minutes for scrapy crawl, 30 seconds for others
    const finalTimeout = timeout || defaultTimeout;

    // デバッグ用ログ
    logger.info(`Request body: ${JSON.stringify(req.body, null, 2)}`);

    // 入力検証
    if (!command) {
      return res.status(400).json({
        success: false,
        error: 'Command is required',
        code: 'MISSING_COMMAND'
      });
    }

    // セキュリティチェック
    const securityCheck = isCommandSafe(command);
    if (!securityCheck.safe) {
      logger.warn(`Blocked unsafe command: ${command} - ${securityCheck.reason}`);
      return res.status(400).json({
        success: false,
        error: 'Command not allowed',
        reason: securityCheck.reason,
        code: 'UNSAFE_COMMAND'
      });
    }

    // 作業ディレクトリの検証
    if (!isWorkingDirectorySafe(workingDir)) {
      return res.status(400).json({
        success: false,
        error: 'Working directory not allowed',
        code: 'UNSAFE_DIRECTORY'
      });
    }

    // 作業ディレクトリの存在確認
    if (!fs.existsSync(workingDir)) {
      return res.status(400).json({
        success: false,
        error: 'Working directory does not exist',
        workingDir,
        code: 'DIRECTORY_NOT_FOUND'
      });
    }

    logger.info(`Executing command: ${command} in ${workingDir}`);

    // コマンド実行
    const options = {
      cwd: workingDir,
      timeout: finalTimeout,
      encoding,
      maxBuffer: 1024 * 1024, // 1MB
      env: getPythonEnvironment(workingDir)
    };

    // Log timeout information for scrapy crawl
    if (isScrapyCrawl) {
      logger.info(`Scrapy crawl command detected. Using extended timeout: ${finalTimeout}ms (${finalTimeout/1000}s)`);
    }

    const { stdout, stderr } = await execAsync(command, options);
    const executionTime = Date.now() - startTime;

    logger.info(`Command completed in ${executionTime}ms`);

    res.json({
      success: true,
      command,
      stdout: stdout || '',
      stderr: stderr || '',
      exitCode: 0,
      executionTime,
      workingDir,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    const executionTime = Date.now() - startTime;

    logger.error(`Command execution failed: ${error.message}`);

    // タイムアウトエラー
    if (error.code === 'ETIMEDOUT') {
      return res.status(408).json({
        success: false,
        error: 'Command execution timed out',
        command: req.body.command,
        timeout: finalTimeout,
        executionTime,
        code: 'TIMEOUT'
      });
    }

    // Scrapyの場合、exit code 0でも stderr に出力があることがある
    // また、CLOSESPIDER_ITEMCOUNTで正常終了した場合もexit code 0以外になることがある
    const isScrapyCommand = req.body.command && req.body.command.includes('scrapy');
    const hasSuccessfulOutput = (error.stdout || error.stderr) && (
      (error.stdout && (
        error.stdout.includes('INFO: Spider opened') ||
        error.stdout.includes('Scraped product:') ||
        error.stdout.includes('closespider_itemcount') ||
        error.stdout.includes('INFO: Closing spider') ||
        error.stdout.includes('item_scraped_count')
      )) ||
      (error.stderr && (
        error.stderr.includes('INFO: Spider opened') ||
        error.stderr.includes('Scraped product:') ||
        error.stderr.includes('closespider_itemcount') ||
        error.stderr.includes('INFO: Closing spider') ||
        error.stderr.includes('item_scraped_count')
      ))
    );

    if (isScrapyCommand && hasSuccessfulOutput) {
      // Scrapyが正常に動作した場合は成功として扱う
      logger.info(`Scrapy execution completed successfully despite non-zero exit code`);
      return res.json({
        success: true,
        command: req.body.command,
        stdout: error.stdout || '',
        stderr: error.stderr || '',
        exitCode: error.code || 0,
        executionTime,
        workingDir: req.body.workingDir,
        timestamp: new Date().toISOString(),
        note: 'Scrapy execution completed successfully (exit code may be non-zero due to item limit or normal termination)'
      });
    }

    // その他のエラー
    res.status(500).json({
      success: false,
      error: error.message,
      command: req.body.command,
      stdout: error.stdout || '',
      stderr: error.stderr || '',
      exitCode: error.code || 1,
      executionTime,
      workingDir: req.body.workingDir,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * @swagger
 * /api/command/spawn:
 *   post:
 *     summary: Spawn a process and stream output
 *     description: Spawn a process with real-time output streaming
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - command
 *             properties:
 *               command:
 *                 type: string
 *                 description: Command to execute
 *               args:
 *                 type: array
 *                 items:
 *                   type: string
 *                 description: Command arguments
 *               workingDir:
 *                 type: string
 *                 description: Working directory
 *               env:
 *                 type: object
 *                 description: Environment variables
 *     responses:
 *       200:
 *         description: Process spawned successfully
 */
router.post('/spawn', (req, res) => {
  try {
    const {
      command,
      args = [],
      workingDir = process.cwd(),
      env = process.env
    } = req.body;

    // セキュリティチェック
    const securityCheck = isCommandSafe(command);
    if (!securityCheck.safe) {
      return res.status(400).json({
        success: false,
        error: 'Command not allowed',
        reason: securityCheck.reason
      });
    }

    // 作業ディレクトリの検証
    if (!isWorkingDirectorySafe(workingDir)) {
      return res.status(400).json({
        success: false,
        error: 'Working directory not allowed'
      });
    }

    logger.info(`Spawning process: ${command} ${args.join(' ')}`);

    // Server-Sent Events (SSE) の設定
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Cache-Control'
    });

    // コマンドの完全パスを取得
    const fullCommand = getCommandPath(command);

    // Python環境を設定
    const pythonEnv = getPythonEnvironment(workingDir);
    const mergedEnv = { ...pythonEnv, ...env };

    const child = spawn(fullCommand, args, {
      cwd: workingDir,
      env: mergedEnv,
      stdio: ['pipe', 'pipe', 'pipe']
    });

    // プロセス開始通知
    res.write(`data: ${JSON.stringify({
      type: 'start',
      pid: child.pid,
      command,
      args,
      workingDir,
      timestamp: new Date().toISOString()
    })}\n\n`);

    // 標準出力
    child.stdout.on('data', (data) => {
      res.write(`data: ${JSON.stringify({
        type: 'stdout',
        data: data.toString(),
        timestamp: new Date().toISOString()
      })}\n\n`);
    });

    // 標準エラー出力
    child.stderr.on('data', (data) => {
      res.write(`data: ${JSON.stringify({
        type: 'stderr',
        data: data.toString(),
        timestamp: new Date().toISOString()
      })}\n\n`);
    });

    // プロセス終了
    child.on('close', (code, signal) => {
      res.write(`data: ${JSON.stringify({
        type: 'close',
        exitCode: code,
        signal,
        timestamp: new Date().toISOString()
      })}\n\n`);
      res.end();
    });

    // エラーハンドリング
    child.on('error', (error) => {
      res.write(`data: ${JSON.stringify({
        type: 'error',
        error: error.message,
        timestamp: new Date().toISOString()
      })}\n\n`);
      res.end();
    });

    // クライアント切断時の処理
    req.on('close', () => {
      if (!child.killed) {
        child.kill();
        logger.info(`Process ${child.pid} killed due to client disconnect`);
      }
    });

  } catch (error) {
    logger.error(`Spawn error: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @swagger
 * /api/command/sync:
 *   post:
 *     summary: Execute a command synchronously
 *     description: Execute a command synchronously and return result immediately
 */
router.post('/sync', (req, res) => {
  const startTime = Date.now();

  try {
    const {
      command,
      workingDir = process.cwd(),
      encoding = 'utf8',
      timeout = 10000
    } = req.body;

    // 入力検証
    if (!command) {
      return res.status(400).json({
        success: false,
        error: 'Command is required'
      });
    }

    // セキュリティチェック
    const securityCheck = isCommandSafe(command);
    if (!securityCheck.safe) {
      return res.status(400).json({
        success: false,
        error: 'Command not allowed',
        reason: securityCheck.reason
      });
    }

    logger.info(`Executing sync command: ${command}`);

    const result = execSync(command, {
      cwd: workingDir,
      encoding,
      timeout,
      maxBuffer: 1024 * 1024,
      env: getPythonEnvironment(workingDir)
    });

    const executionTime = Date.now() - startTime;

    res.json({
      success: true,
      command,
      output: result.toString(),
      executionTime,
      workingDir,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    const executionTime = Date.now() - startTime;

    res.status(500).json({
      success: false,
      error: error.message,
      command: req.body.command,
      output: error.stdout ? error.stdout.toString() : '',
      stderr: error.stderr ? error.stderr.toString() : '',
      executionTime,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * @swagger
 * /api/command/allowed:
 *   get:
 *     summary: Get list of allowed commands
 *     description: Returns the list of commands that are allowed to be executed
 */
router.get('/allowed', (req, res) => {
  res.json({
    success: true,
    allowedCommands: ALLOWED_COMMANDS,
    blockedPatterns: BLOCKED_PATTERNS.map(pattern => pattern.toString()),
    securityInfo: {
      maxTimeout: 30000,
      maxBuffer: '1MB',
      allowedDirectories: ['/tmp', '/home', 'current working directory', '/var/tmp']
    }
  });
});

module.exports = router;
