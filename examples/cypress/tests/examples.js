describe('Example', function () {
  it('should pass.', () => {
    TBCS_DESCRIPTION('Simple test example.');
    TBCS_AUTID('CY-SAMPLE-TEST-01');
    cy.log('should pass')
    expect(true).to.equal(true)
  });

  it('should fail.', () => {
    TBCS_DESCRIPTION('Simple test example.');
    TBCS_AUTID('CY-SAMPLE-TEST-02');
    cy.log('should fail')
    cy.wrap('Failing chainable').then(_ => { throw new Error('test fails here') })
  });
})
