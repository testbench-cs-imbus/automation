import moment = require('moment');
import { ReportTestCase, ReportTestCommand, ReportTestSuite } from './interfaces/report.interfaces';
import { Result, TestBenchOptions, TestBenchTestCase } from './interfaces/tbcs.interfaces';
import { ReportLogger } from './report.logger';
import { TestBenchAutomation } from './tbcs.publish';

const TEST_RESULT_FOLDER = 'test-results';

const loggedCommands = new Set<ReportTestCommand>();
const loggedMetaCommands = new Set<ReportTestCommand>();
const reportTestSuites = new Set<ReportTestSuite>();

const getFilePath = filename => `${TEST_RESULT_FOLDER}/${filename}`;
const getSpecName = () => window.location.pathname.replace('/__cypress/iframes/integration/', '');
const timeToSeconds = time => Number(time / 1000).toFixed(2);

// tbcs execution result import specific
const reporterOptions = Cypress.config('reporterOptions') as TestBenchOptions;
const tbcsAutomation: TestBenchAutomation = new TestBenchAutomation(reporterOptions);
var alreadyLoggedIn: boolean = false;

// callbacks
function beforeEachTest() {
  loggedCommands.clear();
  loggedMetaCommands.clear();
}

function getOrCreateReportTestSuite(suiteName: string): ReportTestSuite {
  var result: ReportTestSuite = undefined;
  reportTestSuites.forEach(element => {
    if (element.name === suiteName) result = element;
  });
  if (result) return result;

  result = {
    name: suiteName,
    testCases: new Set<ReportTestCase>(),
  };
  reportTestSuites.add(result);
  return result;
}

function getOrCreateReportTestCase(suite: ReportTestSuite, name: string): ReportTestCase {
  var result: ReportTestCase = undefined;
  suite.testCases.forEach(element => {
    if (element.name === name) result = element;
  });
  if (result) return result;

  result = {
    name: name,
  };
  suite.testCases.add(result);
  return result;
}

function startEventListeners() {
  Cypress.on('command:end', ({ attributes }) => {
    // ignore none cy.log commands
    if (attributes.name !== 'log') return;
    // ignore before and after cy-log entries by hook id != r*
    if (attributes.args.length === 0 || !String(attributes.logs[0]._emittedAttrs.hookId).startsWith('r')) return;
    var command: ReportTestCommand = {
      name: attributes.name,
      dateTime: moment().toISOString(),
      content: attributes.args[0],
    };
    var regcat = /((TBCS_AUTID|TBCS_CATEGORY|TBCS_DESCRIPTION)\(.+\))(.*)/;
    if (regcat.test(command.content)) {
      loggedMetaCommands.add(command);
    } else {
      loggedCommands.add(command);
    }
  });
}

function beforeAllTests() {
  reportTestSuites.clear();

  // wait until login finished (the cypress way)
  if (reporterOptions.skipResultImport) return;
  if (!alreadyLoggedIn) {
    cy.wrap('Login to TBCS')
      .then(async () => {
        await tbcsAutomation.Start();
        alreadyLoggedIn = true;
      })
      .then(_ => {
        expect(alreadyLoggedIn).to.be.true;
      });
  }
}

function afterEachTest() {
  var reportSuite = getOrCreateReportTestSuite(String(this.currentTest.parent.title));
  var reportTest = getOrCreateReportTestCase(reportSuite, this.currentTest.title);
  reportTest.commands = new Set<ReportTestCommand>(loggedCommands); // new Set because loggedCommands is const
  reportTest.metaCommands = new Set<ReportTestCommand>(loggedMetaCommands); // new Set because loggedCommands is const
  reportTest.time = this.currentTest.duration;
  reportTest.failed = false;
  if (this.currentTest.state === 'failed') {
    reportTest.failed = true;
    reportTest.error = this.currentTest.err.message;
  }
  this.currentTest.state === 'pending' ? (reportTest.skipped = true) : (reportTest.skipped = false);

  // publish to tbcs
  if (reporterOptions.skipResultImport) return;
  var eid = '';
  loggedMetaCommands.forEach(cmd => {
    var regcat = /(TBCS_AUTID\()(.+)(\).*)/;
    if (regcat.test(cmd.content)) {
      eid = cmd.content.match(regcat)[2];
    }
  });
  var descr = '';
  loggedMetaCommands.forEach(cmd => {
    var regcat = /(TBCS_DESCRIPTION\()(.+)(\).*)/;
    if (regcat.test(cmd.content)) {
      descr = cmd.content.match(regcat)[2];
    }
  });
  var steps: Array<string> = [];
  loggedCommands.forEach(cmd => {
    steps.push(cmd.content);
  });
  var tbcsTestCase: TestBenchTestCase = {
    name: reportTest.name,
    description: descr,
    externalId: eid,
    testSteps: steps,
  };
  // run the import not asyncronous to prevent writing results to wrong test cases (humbled external id's)
  cy.wrap('Sending result to TBCS')
    .then(async () => {
      await tbcsAutomation.PublishAutomatedTest(tbcsTestCase, reportTest.failed ? Result.Failed : Result.Passed);
    })
    .then(_ => {
      expect(true).to.equal(true);
    });
}

// https://github.com/junit-team/junit5/blob/master/platform-tests/src/test/resources/jenkins-junit.xsd
// https://llg.cubic.org/docs/junit/
function afterAllTests() {
  try {
    const specName = getSpecName();
    var totalTime = 0;
    var totalTests = 0;
    var failedSuites = 0;

    reportTestSuites.forEach(suite => {
      suite.time = 0;
      suite.testCount = 0;
      suite.failedCount = 0;
      suite.skippedCount = 0;

      suite.testCases.forEach(test => {
        suite.time += test.time;
        suite.testCount += 1;

        if (test.failed) {
          suite.failedCount += 1;
        } else if (test.skipped) {
          suite.skippedCount += 1;
        }
      });

      totalTime += suite.time;
      totalTests += suite.testCount;
      failedSuites += suite.failedCount;
    });

    const totalTimeString = timeToSeconds(totalTime);

    let content = '<?xml version="1.0" encoding="UTF-8"?>\n';
    content += '<testsuites name="Cypress Tests" ';
    content += `time="${totalTimeString}" `;
    content += `tests="${totalTests}" `;
    content += `failures="${failedSuites}">\n`;

    reportTestSuites.forEach(suite => {
      content += `\t<testsuite name="${suite.name}" `;
      content += `timestamp="${new Date().toISOString()}" `;
      content += `tests="${suite.testCount}" `;
      content += `failures="${suite.failedCount}" `;
      content += `skipped="${suite.skippedCount}" `;
      content += `time="${timeToSeconds(suite.time)}">\n`;

      suite.testCases.forEach(test => {
        content += `\t\t<testcase name="${test.name}" `;
        content += `time="${timeToSeconds(test.time)}" `;
        content += `classname="${specName}">\n`;

        test.metaCommands.forEach(cmd => {
          if (cmd.name === 'log') {
            content += '\t\t\t<!--' + cmd.content + '-->\n';
          }
        });

        content += '\t\t\t<system-out>\n';
        content += '\t\t\t<![CDATA[\n';
        test.commands.forEach(cmd => {
          content += '\t\t\t\t' + cmd.content + '\n';
        });
        content += '\t\t\t]]>\n';
        content += '\t\t\t</system-out>\n';

        if (test.failed) {
          content += `\t\t\t<failure><![CDATA[${test.error}]]></failure>\n`;
        }
        if (test.skipped) {
          content += '\t\t\t<skipped />\n';
        }
        content += '\t\t</testcase>\n';
      });

      content += '\t</testsuite>\n';
    });
    content += '</testsuites>';

    const filename = getSpecName().replace(/\//g, '_');
    const filepath = `${getFilePath(filename)}.xml`;
    cy.writeFile(filepath, content);

    // If no tests are run then this could be problem in 'before all' hook
    if (totalTests === 0 && this.currentTest.err) {
      const error = this.currentTest.err;
      const errorFilename = `${getSpecName()}/${error.name}.txt`;
      const erroFilepath = getFilePath(errorFilename);
      cy.writeFile(erroFilepath, error.message);
    }
  } catch (error) {
    ReportLogger.error(error);
  }
  if (reporterOptions.skipResultImport) return;
  // externally called with execution ID?
  if (Cypress.env('extid')) return;
  cy.wrap('Closing TBCS test session.')
    .then(async () => {
      await tbcsAutomation.End();
    })
    .then(_ => {
      expect(true).to.equal(true);
    });
}

startEventListeners();
before(beforeAllTests);
beforeEach(beforeEachTest);
afterEach(afterEachTest);
after(afterAllTests);
