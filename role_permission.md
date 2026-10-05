# Dental Management API - Role Access Matrix

This document maps all OpenAPI paths and HTTP methods against system roles (`Admin`, `Manager`, `Secretary`, `Doctor`, `Assistant`, `Employee`, `Client`).

> **Legend**:
> - :white_check_mark: Allowed / Permitted
> - *(blank)* Denied / Restricted
> - `*` Self-only access (e.g. current logged-in user profile)

---

## 1. Authentication & System Bootstrapping

| Role          | POST `/api/v1/auth/token` | POST `/api/v1/users/bootstrap_user` | POST `/api/v1/users/bootstrap_role` |   GET `/health`    |
| :------------ | :-----------------------: | :---------------------------------: | :---------------------------------: | :----------------: |
| **Admin**     |    :white_check_mark:     |         :white_check_mark:          |         :white_check_mark:          | :white_check_mark: |
| **Manager**   |    :white_check_mark:     |                                     |                                     | :white_check_mark: |
| **Secretary** |    :white_check_mark:     |                                     |                                     | :white_check_mark: |
| **Doctor**    |    :white_check_mark:     |                                     |                                     | :white_check_mark: |
| **Assistant** |    :white_check_mark:     |                                     |                                     | :white_check_mark: |
| **Employee**  |    :white_check_mark:     |                                     |                                     | :white_check_mark: |
| **Client**    |    :white_check_mark:     |                                     |                                     | :white_check_mark: |

---

## 2. Users & Staff Management

| Role          | GET `/api/v1/users/` | POST `/api/v1/users/` | GET `/api/v1/users/me` | GET `/api/v1/users/{id}` | PATCH `/api/v1/users/{id}` | DELETE `/api/v1/users/{id}` | GET `/api/v1/users/{id}/reservations` |
| :------------ | :------------------: | :-------------------: | :--------------------: | :----------------------: | :------------------------: | :-------------------------: | :-----------------------------------: |
| **Admin**     |  :white_check_mark:  |  :white_check_mark:   |   :white_check_mark:   |    :white_check_mark:    |     :white_check_mark:     |     :white_check_mark:      |          :white_check_mark:           |
| **Manager**   |  :white_check_mark:  |  :white_check_mark:   |   :white_check_mark:   |    :white_check_mark:    |     :white_check_mark:     |                             |          :white_check_mark:           |
| **Secretary** |  :white_check_mark:  |                       |   :white_check_mark:   |    :white_check_mark:    |                            |                             |          :white_check_mark:           |
| **Doctor**    |                      |                       |   :white_check_mark:   |   :white_check_mark:*    |                            |                             |          :white_check_mark:*          |
| **Assistant** |                      |                       |   :white_check_mark:   |                          |                            |                             |                                       |
| **Employee**  |                      |                       |   :white_check_mark:   |                          |                            |                             |                                       |
| **Client**    |                      |                       |                        |                          |                            |                             |                                       |

---

## 3. Roles

| Role          | GET `/api/v1/roles/` | POST `/api/v1/roles/` |
| :------------ | :------------------: | :-------------------: |
| **Admin**     |  :white_check_mark:  |  :white_check_mark:   |
| **Manager**   |  :white_check_mark:  |                       |
| **Secretary** |                      |                       |
| **Doctor**    |                      |                       |
| **Assistant** |                      |                       |
| **Employee**  |                      |                       |
| **Client**    |                      |                       |

---

## 4. Persons (Patients & Contacts)

| Role          | GET `/api/v1/persons/` | POST `/api/v1/persons/` | GET `/api/v1/persons/{id}` | PATCH `/api/v1/persons/{id}` | DELETE `/api/v1/persons/{id}` |
| :------------ | :--------------------: | :---------------------: | :------------------------: | :--------------------------: | :---------------------------: |
| **Admin**     |   :white_check_mark:   |   :white_check_mark:    |     :white_check_mark:     |      :white_check_mark:      |      :white_check_mark:       |
| **Manager**   |   :white_check_mark:   |   :white_check_mark:    |     :white_check_mark:     |      :white_check_mark:      |      :white_check_mark:       |
| **Secretary** |   :white_check_mark:   |   :white_check_mark:    |     :white_check_mark:     |      :white_check_mark:      |                               |
| **Doctor**    |   :white_check_mark:   |   :white_check_mark:    |     :white_check_mark:     |      :white_check_mark:      |                               |
| **Assistant** |   :white_check_mark:   |                         |     :white_check_mark:     |                              |                               |
| **Employee**  |                        |                         |                            |                              |                               |
| **Client**    |                        |                         |    :white_check_mark:*     |     :white_check_mark:*      |                               |

---

## 5. Reservations & Appointments

| Role          | GET `/api/v1/reservations/` | POST `/api/v1/reservations/` | GET `/api/v1/reservations/{id}` | PATCH `/api/v1/reservations/{id}` | DELETE `/api/v1/reservations/{id}` |
| :------------ | :-------------------------: | :--------------------------: | :-----------------------------: | :-------------------------------: | :--------------------------------: |
| **Admin**     |     :white_check_mark:      |      :white_check_mark:      |       :white_check_mark:        |        :white_check_mark:         |         :white_check_mark:         |
| **Manager**   |     :white_check_mark:      |      :white_check_mark:      |       :white_check_mark:        |        :white_check_mark:         |         :white_check_mark:         |
| **Secretary** |     :white_check_mark:      |      :white_check_mark:      |       :white_check_mark:        |        :white_check_mark:         |         :white_check_mark:         |
| **Doctor**    |     :white_check_mark:*     |     :white_check_mark:*      |       :white_check_mark:*       |        :white_check_mark:*        |                                    |
| **Assistant** |     :white_check_mark:*     |                              |       :white_check_mark:*       |                                   |                                    |
| **Employee**  |                             |                              |                                 |                                   |                                    |
| **Client**    |     :white_check_mark:*     |      :white_check_mark:      |       :white_check_mark:*       |                                   |                                    |

---

## 6. Quotes & Billing

| Role          | GET `/api/v1/quotes/` | POST `/api/v1/quotes/` | GET `/api/v1/quotes/{id}` | PATCH `/api/v1/quotes/{id}` | DELETE `/api/v1/quotes/{id}` |
| :------------ | :-------------------: | :--------------------: | :-----------------------: | :-------------------------: | :--------------------------: |
| **Admin**     |  :white_check_mark:   |   :white_check_mark:   |    :white_check_mark:     |     :white_check_mark:      |      :white_check_mark:      |
| **Manager**   |  :white_check_mark:   |   :white_check_mark:   |    :white_check_mark:     |     :white_check_mark:      |      :white_check_mark:      |
| **Secretary** |  :white_check_mark:   |   :white_check_mark:   |    :white_check_mark:     |     :white_check_mark:      |                              |
| **Doctor**    |  :white_check_mark:   |   :white_check_mark:   |    :white_check_mark:     |     :white_check_mark:      |                              |
| **Assistant** |  :white_check_mark:   |                        |    :white_check_mark:     |                             |                              |
| **Employee**  |                       |                        |                           |                             |                              |
| **Client**    |  :white_check_mark:*  |                        |    :white_check_mark:*    |                             |                              |

---

## 7. Items & Catalog

| Role          | GET `/api/v1/items/` | POST `/api/v1/items/` | GET `/api/v1/items/{id}` | PATCH `/api/v1/items/{id}` | DELETE `/api/v1/items/{id}` |
| :------------ | :------------------: | :-------------------: | :----------------------: | :------------------------: | :-------------------------: |
| **Admin**     |  :white_check_mark:  |  :white_check_mark:   |    :white_check_mark:    |     :white_check_mark:     |     :white_check_mark:      |
| **Manager**   |  :white_check_mark:  |  :white_check_mark:   |    :white_check_mark:    |     :white_check_mark:     |     :white_check_mark:      |
| **Secretary** |  :white_check_mark:  |                       |    :white_check_mark:    |                            |                             |
| **Doctor**    |  :white_check_mark:  |                       |    :white_check_mark:    |                            |                             |
| **Assistant** |  :white_check_mark:  |                       |    :white_check_mark:    |                            |                             |
| **Employee**  |  :white_check_mark:  |                       |    :white_check_mark:    |                            |                             |
| **Client**    |                      |                       |                          |                            |                             |

---

## 8. Item Categories

| Role          | GET `/api/v1/categories/` | POST `/api/v1/categories/` | GET `/api/v1/categories/{id}` | PATCH `/api/v1/categories/{id}` | DELETE `/api/v1/categories/{id}` |
| :------------ | :-----------------------: | :------------------------: | :---------------------------: | :-----------------------------: | :------------------------------: |
| **Admin**     |    :white_check_mark:     |     :white_check_mark:     |      :white_check_mark:       |       :white_check_mark:        |        :white_check_mark:        |
| **Manager**   |    :white_check_mark:     |     :white_check_mark:     |      :white_check_mark:       |       :white_check_mark:        |        :white_check_mark:        |
| **Secretary** |    :white_check_mark:     |                            |      :white_check_mark:       |                                 |                                  |
| **Doctor**    |    :white_check_mark:     |                            |      :white_check_mark:       |                                 |                                  |
| **Assistant** |    :white_check_mark:     |                            |      :white_check_mark:       |                                 |                                  |
| **Employee**  |    :white_check_mark:     |                            |      :white_check_mark:       |                                 |                                  |
| **Client**    |                           |                            |                               |                                 |                                  |

---

## 9. Print / Document Presets

| Role          | GET `/api/v1/presets/` | POST `/api/v1/presets/` | GET `/api/v1/presets/{id}` | PATCH `/api/v1/presets/{id}` | DELETE `/api/v1/presets/{id}` |
| :------------ | :--------------------: | :---------------------: | :------------------------: | :--------------------------: | :---------------------------: |
| **Admin**     |   :white_check_mark:   |   :white_check_mark:    |     :white_check_mark:     |      :white_check_mark:      |      :white_check_mark:       |
| **Manager**   |   :white_check_mark:   |   :white_check_mark:    |     :white_check_mark:     |      :white_check_mark:      |      :white_check_mark:       |
| **Secretary** |   :white_check_mark:   |                         |     :white_check_mark:     |                              |                               |
| **Doctor**    |   :white_check_mark:   |                         |     :white_check_mark:     |                              |                               |
| **Assistant** |                        |                         |                            |                              |                               |
| **Employee**  |                        |                         |                            |                              |                               |
| **Client**    |                        |                         |                            |                              |                               |

---

## 10. Reminder Preferences

| Role          | GET `/api/v1/reminders/` | POST `/api/v1/reminders/` |
| :------------ | :----------------------: | :-----------------------: |
| **Admin**     |    :white_check_mark:    |    :white_check_mark:     |
| **Manager**   |    :white_check_mark:    |                           |
| **Secretary** |    :white_check_mark:    |                           |
| **Doctor**    |    :white_check_mark:    |                           |
| **Assistant** |    :white_check_mark:    |                           |
| **Employee**  |                          |                           |
| **Client**    |    :white_check_mark:    |                           |

---

## 11. Data Import & Export

| Role          | POST `/api/v1/import_export/export/{entity}` | POST `/api/v1/import_export/validate/{entity}` | POST `/api/v1/import_export/commit/{entity}` |
| :------------ | :------------------------------------------: | :--------------------------------------------: | :------------------------------------------: |
| **Admin**     |              :white_check_mark:              |               :white_check_mark:               |              :white_check_mark:              |
| **Manager**   |              :white_check_mark:              |               :white_check_mark:               |              :white_check_mark:              |
| **Secretary** |                                              |                                                |                                              |
| **Doctor**    |                                              |                                                |                                              |
| **Assistant** |                                              |                                                |                                              |
| **Employee**  |                                              |                                                |                                              |
| **Client**    |                                              |                                                |                                              |