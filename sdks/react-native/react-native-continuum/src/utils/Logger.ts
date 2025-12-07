/**
 * Logger - Configurable logging utility
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'silent';

export class Logger {
  private level: LogLevel;
  private levelPriority: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3,
    silent: 4,
  };

  constructor(level: LogLevel = 'info') {
    this.level = level;
  }

  setLevel(level: LogLevel): void {
    this.level = level;
  }

  debug(message: string, meta?: any): void {
    this.log('debug', message, meta);
  }

  info(message: string, meta?: any): void {
    this.log('info', message, meta);
  }

  warn(message: string, meta?: any): void {
    this.log('warn', message, meta);
  }

  error(message: string, error?: any): void {
    this.log('error', message, error);
  }

  private log(level: LogLevel, message: string, meta?: any): void {
    if (this.levelPriority[level] < this.levelPriority[this.level]) {
      return;
    }

    const timestamp = new Date().toISOString();
    const prefix = `[CONTINUUM] [${timestamp}] [${level.toUpperCase()}]`;

    const logMessage = meta
      ? `${prefix} ${message} ${JSON.stringify(meta)}`
      : `${prefix} ${message}`;

    switch (level) {
      case 'debug':
      case 'info':
        console.log(logMessage);
        break;
      case 'warn':
        console.warn(logMessage);
        break;
      case 'error':
        console.error(logMessage);
        break;
    }
  }
}
