// these function declarations are used to provide meta data information for TBCS import.
declare function TBCS_CATEGORY(value: string): void;
declare function TBCS_DESCRIPTION(value: string): void;
declare function TBCS_AUTID(value: string): void;

// INFO: Categories should be handled per test spec file
globalThis.TBCS_CATEGORY = (value: string) => {
  cy.log('TBCS_CATEGORY(' + value + ')');
};

globalThis.TBCS_DESCRIPTION = (value: string) => {
  cy.log('TBCS_DESCRIPTION(' + value + ')');
};

globalThis.TBCS_AUTID = (value: string) => {
  cy.log('TBCS_AUTID(' + value + ')');
};
