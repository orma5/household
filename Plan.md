1. New Data Model: Account
  We will create a new model (likely in common/models.py) to represent the "Household" or "Organization".
   * Fields: name, owner (FK to User).
   * Concept: The Account owns the data. The User belongs to the Account.

  2. Update Relationships
   * Profile: Add an account ForeignKey. This links a User to a specific Account.
   * Location: Replace the user field with an account field.
   * Item/Task: Logic will be updated to check the Account of the current user, rather than the user ID itself.

  3. Data Migration (Important)
  I will write a migration to ensure existing data is preserved:
   1. For every existing User, create a new Account (e.g., "John's Household").
   2. Link the User to that Account.
   3. Transfer ownership of their Locations to that Account.

  4. Admin Features
  We will need a to update the settings page where the Account Owner can:
   * View members.
   * Invite new users (for now, we can implement a simple "Add User" form that creates a user and links them to the account, or generates a registration link).
   * Update the household name in a section on the top of the page
