describe('Login', function () {
  it('page contains specified elements.', () => {
    TBCS_DESCRIPTION('Test that the login page contains required elements.');
    TBCS_AUTID('CY-SAMPLE-LOGIN-01');

    cy.log('Go to the login page.');
    cy.visit('/login');

    cy.log('Check that the login field for "Username" is displayed.');
    cy.get('[id=input_username]').should('be.visible');
    cy.log('Check that the login field for "Password" is displayed.');
    cy.get('[id=input_password]').should('be.visible');
    cy.log('Check that the "Login" button is displayed.');
    cy.get('[id=button_login]').should('be.visible');
  });

  it('page can be switched to german language.', () => {
    TBCS_DESCRIPTION('Test that the login page allows switching the language.');
    TBCS_AUTID('CY-SAMPLE-LOGIN-02');

    cy.log('Go to the login page.');
    cy.visit('/login');

    cy.log('Click the "german flag button" to switch to the german language.');
    cy.get('[id=german]').should('be.visible').click();

    cy.log('Check that the login button is labeled with "Anmelden" correctly.');
    cy.get('[id=button_login]').should('be.visible').should('have.text', ' Anmelden ');
  });

  it('without credentials as vendor on the page is successful.', () => {
    TBCS_DESCRIPTION('Test that the login is working.');
    TBCS_AUTID('CY-SAMPLE-LOGIN-03');

    cy.log('Go to the login page.');
    cy.visit('/login');

    cy.log('Login as vendor without credentials.');
    cy.get('[id=login_as_vendor]').should('be.visible').click();

    cy.log('Check that the customer list is available.');
    cy.get('[id=navigationbar_customer_list]').should('be.visible');

    cy.log('Click the logout button.');
    cy.get('[id=navigationbar_logout]').should('be.visible').click();
  });
})
