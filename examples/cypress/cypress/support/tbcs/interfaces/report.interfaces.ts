export interface ReportTestSuite {
  name: string;
  time?: number;
  testCount?: number;
  failedCount?: number;
  skippedCount?: number;
  testCases?: Set<ReportTestCase>;
}

export interface ReportTestCase {
  name: string;
  time?: number;
  failed?: boolean;
  skipped?: boolean;
  error?: string;
  commands?: Set<ReportTestCommand>;
  metaCommands?: Set<ReportTestCommand>;
}

export interface ReportTestCommand {
  dateTime: string;
  name: string;
  content: string;
}
