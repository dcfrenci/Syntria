
# Quote 
<!-- * In the new/edit quote we shouldn't see the doctors that are not active -->
<!-- * The admin person/user should be hided from the quote page and only the admin should be able to see him -->
<!-- * Allow the GET /presets request to allow client/employee to see the preview and print his quotes -->
<!-- * For doctors allow to see just his patients quote and not every quote in the system -->
<!-- * Doctors can't select doctor in new/edit/delete quote. If they shouldn't hide the buttons -->
<!-- * Assistant shouldn't be able to see the quote page for every patient, just his page -->

# Agenda
<!-- * The seed_data reservation should be flexible with the dates: it shouldn't use the same date each time -->
<!-- * In the reservation dialog it shouldn't accept negative value for the duration -->
* Actually implement the service selection in the reservation (backend and frontend support)
<!-- * Add a way to select a different week in for the agenda page (not scrolling all the weeks needed to get to the desired date) -->
<!-- * Update the seed_data to have all user an appointment in the day current week -->

# Person
<!-- * In the person page fix birt date selection: it shouldn't accept date in wrong format (at the moment: 01/01/275750 is accepted) -> problem just in the frontend -->
<!-- * Make all the details required  -->
<!-- * Admin shouldn't be able to change it's role. We should hide the admin completely ? -->
<!-- * The other role can't change it's role with an higher role (manager -> admin must not be allowed) -->
<!-- * The new reminder preferences button should be hided for everyone except admin -->
<!-- * Hide the Person page for doctors -->
<!-- * To change password for users accounts should ask two times and check if they match -->

# Pricing
<!-- * Add category name in new service dialog  -->
<!-- * When editing/new service we shouldn't have a negative price (the backend should be already okay -> 422 Unprocessable Entity when using negative price) -->
<!-- * Problem with price input 80 become 4.00 sometimes or other strage behavior -->
<!-- * The service table should be ordered by categories when no search is initialized -->
<!-- * Create not active category in seed_data -->
<!-- * Make not active category not choosable in the application. Same with services that are not active -->
<!-- * Delete button category not working -->

# Preset
<!-- * Add the preview button in the presets page with default quote too see and select the wanted preset -->
<!-- * Change the appearance of Client name in the actual quote (Mr. Ms. Mario Rossi -> Mario Rossi -->
<!-- * Problem with the slider after zooming in the page preset. I can't see or slide to the left, just on the right -->
<!-- * Hide the buttons for doctor except preview -->
<!-- * The secretary should be able to PATCH a preset -->

# General
<!-- * The dialog confirmation should show problem if it makes forbidden request and close the dialog instead of staying open for infite time -->

# Style
<!-- * uniform data input style -->
<!-- * adding logo in the login screen and in the app -->