const axios = require('axios');
import { TestBenchApiSession, TestBenchOptions, TestBenchTestSessionExecution, TestBenchTestSessionExecutions } from './interfaces/tbcs.interfaces';
import { ReportLogger } from './report.logger';

export class TestBenchApi {
  private apiSession: TestBenchApiSession = undefined;

  constructor(private options: TestBenchOptions, apiSession: TestBenchApiSession = null) {
    if (apiSession != null) {
      this.apiSession = apiSession
    }
  }

  private apiUrl(): string {
    if (Cypress.env('tbcsurl')) return Cypress.env('tbcsurl') + '/api'
    return this.options.serverUrl + '/api';
  }

  private productUrl(suffix: string) {
    return this.apiUrl() + '/tenants/' + this.apiSession.tenantId + '/products/' + this.apiSession.productId + suffix;
  }

  private testSessionUrl(suffix: string) {
    return this.apiUrl() + '/tenants/' + this.apiSession.tenantId + '/products/' + this.apiSession.productId + '/planning/sessions' + suffix;
  }

  private apiTokenHeaders() {
    return { 'Content-Type': 'application/json', Authorization: `Bearer ${this.apiSession.accessToken}` };
  }

  public login() {
    ReportLogger.info('TestBenchApi.login()');
    return axios({
      method: 'post',
      url: this.apiUrl() + '/tenants/login/session',
      headers: { 'Content-Type': 'application/json' },
      data: {
        tenantName: this.options.workspace,
        force: true,
        login: this.options.username,
        password: this.options.password,
      },
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
        this.apiSession = {
          accessToken: response.data.sessionToken,
          tenantId: response.data.tenantId,
          productId: this.options.productId,
          userId: response.data.userId,
        };
        return this.apiSession;
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public async logout() {
    ReportLogger.info(`TestBenchApi.logout()`);
    return axios({
      method: 'delete',
      url: this.apiUrl() + '/tenants/' + this.apiSession.tenantId + '/login/session',
      headers: this.apiTokenHeaders(),
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
        this.apiSession = undefined;
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public createTestSession(sessionName: string) {
    ReportLogger.info(`TestBenchApi.createTestSession(name: ${sessionName})`);
    return axios({
      method: 'post',
      url: this.testSessionUrl('/v1'),
      headers: this.apiTokenHeaders(),
      data: { name: sessionName },
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
        return response.data.testSessionId;
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public joinTestSessionSelf(sessionId: string) {
    ReportLogger.info(`TestBenchApi.joinTestSession(sessionId: ${sessionId})`);
    return axios({
      method: 'patch',
      url: this.testSessionUrl('/' + sessionId + '/participant/self/v1'),
      headers: this.apiTokenHeaders(),
      data: { active: true },
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public updateTestSession(testCaseId, executionId, testSessionId) {
    ReportLogger.info(`TestBenchApi.updateTestSession(testCaseId: ${JSON.stringify(testCaseId)}, executionId: ${JSON.stringify(executionId)})`);
    let execution: TestBenchTestSessionExecution = {
      testCaseIds: { testCaseId: testCaseId },
      executionId: executionId,
    };
    let executions: TestBenchTestSessionExecutions = {
      addExecutions: [execution],
    };
    return axios({
      method: 'patch',
      url: this.testSessionUrl('/' + testSessionId + '/assign/executions/v1'),
      headers: this.apiTokenHeaders(),
      data: executions,
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response.data));
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public patchTestSession(testSessionId: string, sessionData: any) {
    ReportLogger.info(`TestBenchApi.patchTestSession(${JSON.stringify(sessionData)})`);
    return axios({
      method: 'patch',
      url: this.testSessionUrl('/' + testSessionId + '/v1'),
      headers: this.apiTokenHeaders(),
      data: sessionData,
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response.data));
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public getTestCaseByExternalId(externalId: string): string {
    ReportLogger.info(`TestBenchApi.getTestCaseByExternalId(testCase.externalId: ${externalId})`);
    if (externalId === undefined) return undefined;
    return axios({
      method: 'get',
      url: this.productUrl('/elements?fieldValue=externalId%3Aequals%3A' + externalId + '&types=TestCase'),
      headers: this.apiTokenHeaders(),
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
        if (response.data.elements.length !== 1) return undefined;
        return response.data.elements[0].TestCaseSummary.id;
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public getTestCaseById(testCaseId: string) {
    ReportLogger.info(`TestBenchApi.getTestCaseById(testCaseId: ${testCaseId})`);
    return axios({
      method: 'get',
      url: this.productUrl('/specifications/testCases/' + testCaseId),
      headers: this.apiTokenHeaders(),
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response.data));
        return response.data;
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public deleteTestStep(testCaseId: string, testStepId: string) {
    ReportLogger.info(`TestBenchApi.deleteTestStep(testCaseId: ${testCaseId}, testStepId: ${testStepId})`);
    return axios({
      method: 'delete',
      url: this.productUrl('/specifications/testCases/' + testCaseId + '/testSteps/' + testStepId),
      headers: this.apiTokenHeaders(),
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public createTestCase(testCaseName: string, type: string): string {
    ReportLogger.info(`TestBenchApi.createTestCase(testCaseName: ${testCaseName})`);
    return axios({
      method: 'post',
      url: this.productUrl('/specifications/testCases'),
      headers: this.apiTokenHeaders(),

      data: {
        name: testCaseName,
        testCaseType: type,
      },
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
        return response.data.testCaseId;
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public patchTestCase(testCaseId: string, patchData: any): string {
    ReportLogger.info(`TestBenchApi.patchTestCase(testCaseId: ${testCaseId}), data: ${JSON.stringify(patchData)}`);
    return axios({
      method: 'patch',
      url: this.productUrl('/specifications/testCases/' + testCaseId),
      headers: this.apiTokenHeaders(),
      data: patchData,
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
        return response.data.testCaseId;
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public createTestStepBlock(testCaseId: string, blockTitle: string): number {
    ReportLogger.info(`TestBenchApi.createTestStepBlock(testCaseId: ${testCaseId}, blockTitle: ${blockTitle})`);
    return axios({
      method: 'post',
      url: this.productUrl('/specifications/testCases/' + testCaseId + '/testStepBlocks'),
      headers: this.apiTokenHeaders(),

      data: {
        title: blockTitle,
      },
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
        return response.data.testStepBlockId;
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public deleteTestStepBlock(testCaseId: string, testBlockId: number) {
    ReportLogger.info(`TestBenchApi.deleteTestStepBlock(testCaseId: ${testCaseId}, testBlockId: ${testBlockId})`);
    return axios({
      method: 'delete',
      url: this.productUrl('/specifications/testCases/' + testCaseId + '/testStepBlocks/' + testBlockId),
      headers: this.apiTokenHeaders(),
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public createTestStep(testCaseId: string, testStepName: string, type: string, blockId: number): string {
    ReportLogger.info(`TestBenchApi.createTestStep(testCaseId: ${testCaseId}, testStepName: ${testStepName})`);
    return axios({
      method: 'post',
      url: this.productUrl('/specifications/testCases/' + testCaseId + '/testSteps'),
      headers: this.apiTokenHeaders(),

      data: {
        testStepType: type,
        testStepBlock: 'Test',
        testStepBlockId: blockId,
        description: testStepName,
      },
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
        return response.data.testStepId;
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public putPreconditionMarker(testCaseId: string, empty: boolean) {
    ReportLogger.info(`TestBenchApi.putPreconditionMarker(testCaseId: ${testCaseId}, empty: ${empty})`);
    return axios({
      method: 'put',
      url: this.productUrl('/specifications/testCases/' + testCaseId + '/preconditions/emptyMarker'),
      headers: this.apiTokenHeaders(),
      data: empty,
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public createTestCaseExecution(testCaseId: string): string {
    ReportLogger.info(`TestBenchApi.createTestCaseExecution(testCaseId: ${testCaseId})`);
    return axios({
      method: 'post',
      url: this.productUrl('/executions/testCases/' + testCaseId + '/v1'),
      headers: this.apiTokenHeaders(),
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
        return response.data;
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  // result: Valid values are: "Pending", "Passed", "Failed" or "Calculated"
  public updateExecutionResult(testCaseId: string, executionId: string, result: string) {
    ReportLogger.info(`TestBenchApi.updateExecutionResult(testCaseId: ${testCaseId}, executionId: ${executionId}, result: ${result})`);
    return axios({
      method: 'patch',
      url: this.productUrl('/executions/testCases/' + testCaseId + '/executions/' + executionId + '/v1'),
      headers: this.apiTokenHeaders(),
      data: `{ "executionResult": ${result} }`,
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  // status: Valid values are: "New", "InProgress", "Blocked", "Paused", "Finished", "Closed"
  public updateExecutionStatus(testCaseId: string, executionId: string, status: string) {
    ReportLogger.info(`TestBenchApi.updateExecutionStatus(testCaseId: ${testCaseId}, executionId: ${executionId}, status: ${status})`);
    return axios({
      method: 'put',
      url: this.productUrl('/executions/testCases/' + testCaseId + '/executions/' + executionId + '/status/v1'),
      headers: this.apiTokenHeaders(),
      data: `{ "status": ${status} }`,
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }

  public assignTestStepExecutionResult(testCaseId: string, executionId: string, testStepId: string, result: string) {
    ReportLogger.info(
      `TestBenchApi.assignTestStepExecutionResult(testCaseId: ${testCaseId}, executionId: ${executionId}, testStepId: ${testStepId}, result: ${result})`,
    );
    return axios({
      method: 'patch',
      url: this.productUrl('/executions/testCases/' + testCaseId + '/executions/' + executionId + '/testSteps/' + testStepId + '/v1'),
      headers: this.apiTokenHeaders(),
      data: `{ "result": ${result} }`,
    })
      .then(response => {
        ReportLogger.debug(JSON.stringify(response));
      })
      .catch(error => ReportLogger.error(JSON.stringify(error)));
  }
}
