import moment = require('moment');
import { Result, TestBenchApiSession, TestBenchOptions, TestBenchTestCase, TestStep, TestStepResult } from './interfaces/tbcs.interfaces';
import { ReportLogger } from './report.logger';
import { TestBenchApi } from './tbcs.api';

export class TestBenchAutomation {
  private apiSession: TestBenchApiSession = undefined;
  private testSessionId: string = undefined;
  private tbcsApi: TestBenchApi = undefined;
  private sessionFileName = 'testSessionId.txt';

  constructor(private options: TestBenchOptions) {
    this.tbcsApi = new TestBenchApi(options);
  }

  public async Start() {
    ReportLogger.info('TestBenchAutomation.Start()');
    try {
      if (Cypress.env('sessiontoken')) {
        this.apiSession = {
          accessToken: Cypress.env('sessiontoken'),
          tenantId: Cypress.env('tenantid'),
          productId: Cypress.env('productid'),
          userId: -1,
        };
        this.tbcsApi = new TestBenchApi(this.options, this.apiSession);
        ReportLogger.info('Using existing session token: ' + this.apiSession.accessToken + ' and tenant id: ' + this.apiSession.tenantId);
      } else {
        this.apiSession = await this.tbcsApi.login();
      }
      cy.task('readFileMaybe', this.sessionFileName).then(async res => {
        ReportLogger.debug('Read sessionID: ' + res);
        this.testSessionId = String(res);
        if (this.testSessionId !== 'null') {
          ReportLogger.info('Using existing sessionId: ' + this.testSessionId);
          return;
        }
        let sessionName = this.options.testSessionPrefix + '_' + moment().toISOString();
        this.testSessionId = await this.tbcsApi.createTestSession(sessionName);

        await this.tbcsApi.joinTestSessionSelf(this.testSessionId);
        let sessionData = {
          status: 'InProgress',
        };
        await this.tbcsApi.patchTestSession(this.testSessionId, sessionData);
        ReportLogger.debug('Writing sessionID: ' + this.testSessionId + ' to file: ' + this.sessionFileName);
        cy.writeFile(this.sessionFileName, String(this.testSessionId), 'utf8').then(() => ReportLogger.debug('Session id file written.'));
      });
    } catch (error) {
      ReportLogger.error(error);
    }
  }

  public async End() {
    ReportLogger.info('TestBenchAutomation.End()');
    if (Cypress.env('sessiontoken')) return; // triggered externally
    try {
      let sessionData = {
        status: 'Completed',
      };
      await this.tbcsApi.patchTestSession(this.testSessionId, sessionData);
      await this.tbcsApi.logout();
    } catch (error) {
      ReportLogger.error(error);
    }
  }

  public async PublishAutomatedTest(testCase: TestBenchTestCase, result?: Result) {
    ReportLogger.info(`TestBenchAutomation.runAutomatedTest(testCase: ${JSON.stringify(testCase)}), status: ${JSON.stringify(result)}`);
    try {
      // if test case already exists with the externalId, update test steps
      var testStepsCurrent: Array<TestStep> = []; // remember test steps with id's for later execution results
      let testCaseId = await this.tbcsApi.getTestCaseByExternalId(testCase.externalId);
      // update/create test case?
      let testCaseResponse = undefined;
      if (testCaseId !== undefined) {
        testCaseResponse = await this.tbcsApi.getTestCaseById(testCaseId);
        for (let block of testCaseResponse.testSequence.testStepBlocks) {
          ReportLogger.debug('Scanning test step block: ' + block.title)
          if (block.title === 'Test Steps') {
            for (let step of block.steps) {
              testStepsCurrent.push({
                id: step.id,
                type: step.testStepType,
                blockId: block.id,
                name: step.description,
              });
            }
          }
        }
        if (this.options.skipTestCaseUpdates !== true && this.hasTestStepsChanged(testCase, testCaseResponse)) {
          ReportLogger.info('Updating changed test case.');
          // delete all existing steps and create them new, only from test step block 'Test' expecting an structured test case
          var blockId = -1;
          for (let block of testCaseResponse.testSequence.testStepBlocks) {
            blockId = block.id;
            for (let step of block.steps) {
              await this.tbcsApi.deleteTestStep(testCaseId, step.id);
            }
            await this.tbcsApi.deleteTestStepBlock(testCaseId, blockId);
          }
          // create test steps and remember id's
          blockId = await this.tbcsApi.createTestStepBlock(testCaseId, "Test Steps");
          testStepsCurrent = [];
          for (let step of testCase.testSteps) {
            let stepId = await this.tbcsApi.createTestStep(testCaseId, step, "TestStep", blockId);
            testStepsCurrent.push({
              id: stepId,
              blockId: blockId,
              type: "TestStep",
              name: step,
            });
          }

          let patchData = {
            description: { text: testCase.description ? testCase.description : null },
            responsibles: [this.apiSession.userId],
            isAutomated: true,
            toBeReviewed: true,
          };

          await this.tbcsApi.patchTestCase(testCaseId, patchData);
        }
      } else {
        if (this.options.skipTestCaseUpdates === true) {
          ReportLogger.warn('Test case not found and updates disabled. Skipping result import.');
          return;
        }
        ReportLogger.info('Creating new test case.');
        // create it as a free structured test case
        testCaseId = await this.tbcsApi.createTestCase(testCase.name, 'StructuredTestCase');
        // update for automation
        let patchData = {
          description: { text: testCase.description ? testCase.description : null },
          responsibles: [this.apiSession.userId],
          isAutomated: true,
          toBeReviewed: true,
          externalId: { value: testCase.externalId ? testCase.externalId : null },
        };

        await this.tbcsApi.patchTestCase(testCaseId, patchData);
        await this.tbcsApi.putPreconditionMarker(testCaseId, true);

        // test step block
        blockId = await this.tbcsApi.createTestStepBlock(testCaseId, "Test");
        // test steps
        for (let step of testCase.testSteps) {
          let stepId = await this.tbcsApi.createTestStep(testCaseId, step, "TestStep", blockId);
          testStepsCurrent.push({
            id: stepId,
            blockId: blockId,
            type: "TestStep",
            name: step,
          });
        }
      }

      // add execution
      let executionId = "";
      if (Cypress.env('extid')) {
        executionId = Cypress.env('extid');
      } else {
        executionId = await this.tbcsApi.createTestCaseExecution(testCaseId);
      }
      if (Cypress.env('sessiontoken')) { // triggered externally
        await this.tbcsApi.updateExecutionStatus(testCaseId, executionId, '"InProgress"');
      } else {
        await this.tbcsApi.updateTestSession(testCaseId, executionId, this.testSessionId);
        await this.tbcsApi.updateExecutionStatus(testCaseId, executionId, '"InProgress"');
      }

      if (this.options.skipTestCaseUpdates === true && this.hasTestStepsChanged(testCase, testCaseResponse)) {
        ReportLogger.warn('Test case has changed. Only setting test case result without step results.');
        let patchData = {
          toBeReviewed: true,
        };

        await this.tbcsApi.patchTestCase(testCaseId, patchData);
        await this.tbcsApi.updateExecutionResult(testCaseId, executionId, result);
      } else {
        var testStepResults: TestStepResult[] = [];
        for (let step of testStepsCurrent) {
          testStepResults.push({
            testStepId: step.id,
            result: Result.Passed,
          });
        }
        if (result === Result.Failed) {
          testStepResults[testStepResults.length - 1] ? (testStepResults[testStepResults.length - 1].result = Result.Failed) : null;
        }
        for (let step of testStepResults) {
          await this.tbcsApi.assignTestStepExecutionResult(testCaseId, executionId, step.testStepId, step.result);
        }
        await this.tbcsApi.updateExecutionResult(testCaseId, executionId, result);
      }
    } catch (error) {
      ReportLogger.error(error);
    }
  }

  private hasTestStepsChanged(cypressTestCase: TestBenchTestCase, tbcsTestCase: any): boolean {
    let tbcsSteps = undefined;
    for (let block of tbcsTestCase.testSequence.testStepBlocks) {
      if (block.title === 'Test Steps') {
        tbcsSteps = block.steps;
      }
    }
    if (tbcsSteps === undefined && cypressTestCase.testSteps.length > 0) return true
    if (tbcsSteps !== undefined && cypressTestCase.testSteps.length !== tbcsSteps.length) return true;

    var compareFailed = false;

    cypressTestCase.testSteps.forEach((value, index) => {
      if (String(value).valueOf().localeCompare(String(tbcsSteps[index].description).valueOf()) !== 0) {
        compareFailed = true;
        return;
      }
    });
    return compareFailed;
  }
}
