import moment = require('moment');

export enum LogLevel {
  DEBUG = 4,
  INFO = 3,
  WARN = 2,
  ERROR = 1,
}
export class ReportLogger {
  private static TEST_RESULT_FOLDER = 'test-results';
  private static LOG_FILENAME = 'reporter.log';
  private static ERRORFLAG_FILENAME = 'reportingError';
  private static LOG_LEVEL: LogLevel = LogLevel.INFO;

  public static setlevel(level: LogLevel) {
    ReportLogger.LOG_LEVEL = level;
  }

  public static info(msg: string) {
    ReportLogger.LOG_LEVEL >= LogLevel.INFO ? ReportLogger.log('INFO', msg) : null;
  }

  public static debug(msg: string) {
    ReportLogger.LOG_LEVEL >= LogLevel.DEBUG ? ReportLogger.log('DEBUG', msg) : null;
  }

  public static warn(msg: string) {
    ReportLogger.LOG_LEVEL >= LogLevel.WARN ? ReportLogger.log('WARN', msg) : null;
  }

  public static error(msg: string) {
    ReportLogger.LOG_LEVEL >= LogLevel.ERROR ? ReportLogger.log('ERROR', msg) : null;
    cy.writeFile(`${ReportLogger.TEST_RESULT_FOLDER}/${ReportLogger.ERRORFLAG_FILENAME}`, '', {
      encoding: 'utf8',
      flag: 'w+',
    }).then(() => ReportLogger.debug('Error flag file written.'));
  }

  private static log(level: string, msg: string) {
    cy.writeFile(`${ReportLogger.TEST_RESULT_FOLDER}/${ReportLogger.LOG_FILENAME}`, moment().toISOString() + '\t' + level + '\t' + msg + '\n', {
      encoding: 'utf8',
      flag: 'as+',
    });
  }
}
