export interface TestBenchOptions {
  serverUrl: string;
  workspace: string;
  username: string;
  password: string;
  productId: number;
  testSessionPrefix: string;
  skipResultImport: boolean;
  skipTestCaseUpdates: boolean;
}

export interface TestBenchApiSession {
  accessToken: string;
  tenantId: number;
  productId: number;
  userId: number;
}
export interface TestBenchTestSessionExecutions {
  addExecutions: Array<TestBenchTestSessionExecution>;
}

export interface TestBenchTestSessionExecution {
  testCaseIds: any;
  executionId: number;
}

export enum Result {
  Failed = '"Failed"',
  Passed = '"Passed"',
  Pending = '"Pending"',
  Calculated = '"Calculated"',
}

export interface TestStepResult {
  testStepId: string;
  result: Result;
}

export interface TestStep {
  id: string;
  type: string;
  blockId: number;
  name: string;
}

export interface TestBenchTestCase {
  externalId: string;
  name?: string;
  description?: string;
  testSteps?: string[];
  overwrite?: boolean;
  markForReview?: boolean;
}
