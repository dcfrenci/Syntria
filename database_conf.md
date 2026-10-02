# Database Initilization
To initialize the database use the following python script.
```bash
python3 scripts/initialize.py --admin-only
```
The script also allows to **prefill** the database with the following data.
```bash
python3 scripts/initialize.py
```
The data that will be loaded using this script are divided into two paragraph based on the option selected during the initialization.

---

## Empty Database

### Reminder
| Name     |
| -------- |
| Sms      |
| WhatsApp |
| Telegram |

### Persons
| Name  | Surname | Email           | Birthdate  | Phone      | Reminder pref ID |
| ----- | ------- | --------------- | ---------- | ---------- | ---------------- |
| Admin | System  | admin@email.com | 01/01/0001 | 0000000000 | (Sms)            |

### Role
| Name      | Restricted Access Power |
| --------- | ----------------------- |
| Admin     | 0                       |
| Manager   | 1                       |
| Secretary | 3                       |
| Doctor    | 3                       |
| Assistant | 3                       |
| Emploee   | 4                       |
| Client    | 10                      |

### Users
| Person ID      | Role ID | Active | Password |
| -------------- | ------- | ------ | -------- |
| (Admin System) | admin   | True   | asTf82#1 |


---

## Database Prefill

### Persons
| Name       | Surname     | Email                      | Birthdate  | Phone      | Reminder pref ID |
| ---------- | ----------- | -------------------------- | ---------- | ---------- | ---------------- |
| Francesco  | Della Casa  | francesco@gmai.com         | 01/01/2000 | 3701307257 | (WhatsApp)       |
| Antonietta | Della Bella | antonella@email.com        | 01/02/1988 | 3390007257 | (Telegram)       |
| Matteo     | Bergamaschi | matteo.b@gmail.com         | 15/06/1992 | 3471234567 | (Sms)            |
| Giulia     | Rossi       | giulia.rossi@email.com     | 22/10/1995 | 3289876543 | (WhatsApp)       |
| Marco      | Bianchi     | mbianchi88@yahoo.it        | 05/11/1988 | 3334455666 | (Telegram)       |
| Sofia      | Ricci       | s.ricci@gmail.com          | 12/04/2001 | 3517654321 | (WhatsApp)       |
| Alessandro | Romano      | alex.romano@email.com      | 30/08/1979 | 3398877665 | (Sms)            |
| Martina    | Colombo     | marty.colombo@gmail.com    | 17/02/1998 | 3401122334 | (Telegram)       |
| Lorenzo    | Ferrari     | lorenzo.f@email.com        | 09/09/1990 | 3495544332 | (WhatsApp)       |
| Chiara     | Esposito    | chiara.e@yahoo.it          | 25/12/1985 | 3209988776 | (Sms)            |
| Davide     | Marino      | davide.marino@gmail.com    | 03/03/1993 | 3387766554 | (Telegram)       |
| Sara       | Russo       | sara.russo@email.com       | 14/07/2002 | 3456677889 | (WhatsApp)       |
| Luca       | Conti       | luca.conti99@gmail.com     | 28/01/1999 | 3312233445 | (Sms)            |
| Valentina  | Bruno       | vale.bruno@email.com       | 08/05/1991 | 3478899001 | (WhatsApp)       |
| Giuseppe   | Gallo       | ggallo@yahoo.it            | 19/11/1982 | 3291122334 | (Telegram)       |
| Elena      | Costa       | elena.costa@gmail.com      | 11/10/1996 | 3345566778 | (WhatsApp)       |
| Andrea     | Moretti     | a.moretti@email.com        | 14/08/1994 | 3351234567 | (WhatsApp)       |
| Beatrice   | Barbieri    | bea.barbieri@gmail.com     | 03/12/1987 | 3409876543 | (Telegram)       |
| Simone     | Fontana     | simone.f@yahoo.it          | 21/05/1990 | 3281122334 | (Sms)            |
| Silvia     | Rinaldi     | silvia.rinaldi@email.com   | 09/09/1999 | 3475566778 | (WhatsApp)       |
| Giacomo    | Lombardi    | giacomo.lombardi@gmail.com | 27/02/1984 | 3394455667 | (Telegram)       |
| Federica   | Caruso      | fede.caruso@email.com      | 16/11/1993 | 3319988776 | (WhatsApp)       |
| Stefano    | Ferrara     | s.ferrara@yahoo.it         | 08/04/1981 | 3456677889 | (Sms)            |
| Alessia    | Mariani     | alessia.mariani@gmail.com  | 23/07/2001 | 3201122334 | (WhatsApp)       |
| Nicola     | Bianco      | nicola.bianco@email.com    | 11/01/1989 | 3385544332 | (Telegram)       |
| Francesca  | Gatti       | fra.gatti@gmail.com        | 30/10/1997 | 3498899001 | (WhatsApp)       |
| Michele    | Santoro     | michele.santoro@yahoo.it   | 15/06/1975 | 3341122334 | (Sms)            |
| Paola      | Marini      | paola.marini@email.com     | 02/03/1992 | 3479988776 | (Telegram)       |
| Daniele    | Sala        | daniele.sala@gmail.com     | 18/09/1986 | 3284455667 | (WhatsApp)       |
| Laura      | Fiore       | l.fiore@email.com          | 25/12/1995 | 3396677889 | (WhatsApp)       |
| Roberto    | De Luca     | rob.deluca@yahoo.it        | 07/08/1983 | 3335566778 | (Sms)            |
| Cristina   | Martini     | cristina.m@gmail.com       | 12/04/2000 | 3401122334 | (Telegram)       |
| Paolo      | Galli       | paolo.galli@email.com      | 29/01/1978 | 3519988776 | (WhatsApp)       |
| Elisa      | Coppola     | elisa.coppola@gmail.com    | 19/11/1998 | 3295544332 | (Telegram)       |
| Enrico     | Monti       | enrico.monti@yahoo.it      | 05/05/1991 | 3386677889 | (Sms)            |
| Martina    | D'Amico     | marty.damico@email.com     | 14/02/2003 | 3491122334 | (WhatsApp)       |


### Users
| Person ID            | Role ID   | Active | Password |
| -------------------- | --------- | ------ | -------- |
| (Matteo Bergamaschi) | manager   | True   | kL9$zQ2w |
| (Giulia Rossi)       | assistant | True   | pM4@vX7c |
| (Marco Bianchi)      | doctor    | True   | rT2#yN9b |
| (Sofia Ricci)        | doctor    | False  | wE8!qF3m |
| (Alessandro Romano)  | employ    | True   | bV5&cH1k |
| (Martina Colombo)    | client    | True   | xN7*jP4d |
| (Lorenzo Ferrari)    | secretary | False  | gZ3%tR8s |
| (Chiara Esposito)    | client    | True   | mK6^bV2n |
| (Davide Marino)      | client    | True   | qW1$fD5x |
| (Sara Russo)         | client    | True   | vC9@hJ7L |


### Reservations
| Reservation Date         | Duration min. | Description | Patient ID          | Staff IDs                         |
| ------------------------ | ------------- | ----------- | ------------------- | --------------------------------- |
| 2026-10-02T18:29:16.671Z | 30            | description | (Elisa Copolla)     | [(Marco Bianchi), (Giulia Rossi)] |
| 2026-10-03T09:00:00.000Z | 60            | description | (Martina Colombo)   | [(Sofia Ricci), (Giulia Rossi)]   |
| 2026-10-03T10:00:00.000Z | 30            | description | (Lorenzo Ferrari)   | [(Marco Bianchi)]                 |
| 2026-10-03T10:30:00.000Z | 45            | description | (Chiara Esposito)   | [(Marco Bianchi), (Giulia Rossi)] |
| 2026-10-03T11:15:00.000Z | 60            | description | (Davide Marino)     | [(Sofia Ricci)]                   |
| 2026-10-03T14:00:00.000Z | 30            | description | (Sara Russo)        | [(Marco Bianchi), (Giulia Rossi)] |
| 2026-10-04T09:30:00.000Z | 45            | description | (Andrea Moretti)    | [(Marco Bianchi)]                 |
| 2026-10-04T10:15:00.000Z | 90            | description | (Beatrice Barbieri) | [(Marco Bianchi), (Giulia Rossi)] |
| 2026-10-04T11:45:00.000Z | 30            | description | (Simone Fontana)    | [(Marco Bianchi)]                 |
| 2026-10-04T14:30:00.000Z | 60            | description | (Silvia Rinaldi)    | [(Sofia Ricci), (Giulia Rossi)]   |
| 2026-10-05T09:00:00.000Z | 30            | description | (Giacomo Lombardi)  | [(Sofia Ricci)]                   |
| 2026-10-05T09:30:00.000Z | 120           | description | (Federica Caruso)   | [(Sofia Ricci), (Giulia Rossi)]   |
| 2026-10-05T11:30:00.000Z | 45            | description | (Stefano Ferrara)   | [(Marco Bianchi)]                 |
| 2026-10-05T14:00:00.000Z | 60            | description | (Alessia Mariani)   | [(Marco Bianchi), (Giulia Rossi)] |
| 2026-10-06T10:00:00.000Z | 30            | description | (Nicola Bianco)     | [(Marco Bianchi)]                 |
| 2026-10-06T10:30:00.000Z | 45            | description | (Francesca Gatti)   | [(Sofia Ricci), (Giulia Rossi)]   |
| 2026-10-06T11:15:00.000Z | 60            | description | (Michele Santoro)   | [(Marco Bianchi)]                 |
| 2026-10-06T14:00:00.000Z | 30            | description | (Paola Marini)      | [(Marco Bianchi), (Giulia Rossi)] |
| 2026-10-07T09:00:00.000Z | 90            | description | (Daniele Sala)      | [(Sofia Ricci)]                   |
| 2026-10-07T10:30:00.000Z | 45            | description | (Laura Fiore)       | [(Sofia Ricci), (Giulia Rossi)]   |
| 2026-10-07T11:15:00.000Z | 60            | description | (Elisa Coppola)     | [(Sofia Ricci)]                   |


### Categories
| Name                  | Description                                                     | Active |
| --------------------- | --------------------------------------------------------------- | ------ |
| Orthodontics          | Teeth alignment and braces                                      | True   |
| Endodontics           | Root canal therapy and inner tooth treatments                   | True   |
| Periodontics          | Prevention and treatment of gum diseases                        | True   |
| Prosthodontics        | Design and fitting of artificial teeth and crowns               | True   |
| Oral Surgery          | Tooth extractions, wisdom teeth removal and surgical procedures | True   |
| Cosmetic Dentistry    | Aesthetic treatments like veneers and teeth whitening           | True   |
| Pediatric Dentistry   | Comprehensive dental care for children and adolescents          | True   |
| Preventive Dentistry  | Routine cleanings, fluoride treatments and check-ups            | True   |
| Restorative Dentistry | Repairing damaged teeth using fillings and bridges              | True   |
| Implantology          | Surgical placement and restoration of dental implants           | True   |
| Dental Emergency      | Urgent care for severe toothaches and dental trauma             | False  |


### Items
| Name                        | Description                                        | Price | Category ID             | Active | Specific |
| --------------------------- | -------------------------------------------------- | ----- | ----------------------- | ------ | -------- |
| Dental Cleaning             | Remuval of plaque, tartar and bacteria             | 80    | (Cosmetic Dentistry)    | True   | False    |
| Teeth Whitening             | Professional laser bleaching                       | 250   | (Cosmetic Dentistry)    | True   | False    |
| Porcelain Veneers           | Custom ceramic shells for front teeth              | 800   | (Cosmetic Dentistry)    | True   | True     |
| Traditional Metal Braces    | Full arch metal brackets                           | 2500  | (Orthodontics)          | True   | False    |
| Clear Aligners              | Invisible removable aligners                       | 3500  | (Orthodontics)          | True   | True     |
| Root Canal Treatment        | Nerve removal and sealing                          | 450   | (Endodontics)           | True   | True     |
| Endodontic Retreatment      | Revision of a previous root canal                  | 650   | (Endodontics)           | True   | True     |
| Gum Graft Surgery           | Tissue graft for receding gums                     | 950   | (Periodontics)          | True   | True     |
| Deep Scaling                | Deep cleaning under the gumline                    | 150   | (Periodontics)          | True   | False    |
| Zirconia Dental Crown       | Durable tooth-colored cap                          | 650   | (Prosthodontics)        | True   | True     |
| Full Dentures               | Complete removable artificial teeth                | 1200  | (Prosthodontics)        | True   | False    |
| Wisdom Tooth Extraction     | Surgical removal of impacted 3rd molar             | 300   | (Oral Surgery)          | True   | True     |
| Simple Tooth Extraction     | Removal of a fully erupted tooth                   | 120   | (Oral Surgery)          | True   | False    |
| Child Routine Checkup       | Exam and cleaning for under 12s                    | 60    | (Pediatric Dentistry)   | True   | False    |
| Fissure Sealants            | Protective coating for back molars                 | 40    | (Pediatric Dentistry)   | True   | True     |
| Fluoride Application        | Topical enamel strengthening treatment             | 35    | (Preventive Dentistry)  | True   | False    |
| Composite Filling           | Tooth-colored resin restoration                    | 95    | (Restorative Dentistry) | True   | False    |
| Amalgam Filling             | Silver alloy cavity filling                        | 75    | (Restorative Dentistry) | False  | False    |
| Single Dental Implant       | Titanium root placement                            | 1500  | (Implantology)          | True   | True     |
| Emergency Toothache Exam    | Urgent diagnostic visit                            | 50    | (Dental Emergency)      | False  | False    |
| Broken Tooth Repair         | Temporary fracture stabilization                   | 150   | (Dental Emergency)      | False  | True     |
| Ceramic Braces              | Tooth-colored fixed brackets                       | 2800  | (Orthodontics)          | True   | False    |
| Lingual Braces              | Braces hidden behind the teeth                     | 4000  | (Orthodontics)          | True   | True     |
| Retainer Fitting            | Custom removable post-treatment wire               | 150   | (Orthodontics)          | True   | False    |
| Apicoectomy                 | Surgical removal of the tooth root tip             | 850   | (Endodontics)           | True   | True     |
| Pulpotomy                   | Partial nerve removal for primary teeth            | 200   | (Endodontics)           | True   | True     |
| Post and Core Build-up      | Structural support preparation for a crown         | 300   | (Endodontics)           | True   | True     |
| Crown Lengthening           | Reshaping bone and gum tissue                      | 500   | (Periodontics)          | True   | True     |
| Bone Grafting               | Jaw bone augmentation for implants                 | 800   | (Periodontics)          | True   | True     |
| Periodontal Maintenance     | Specialized cleaning for gum disease patients      | 110   | (Periodontics)          | True   | False    |
| Partial Denture             | Removable replacement for several missing teeth    | 750   | (Prosthodontics)        | True   | False    |
| Implant-Supported Bridge    | Bridge fixed directly to surgical implants         | 2200  | (Prosthodontics)        | True   | True     |
| Dental Flipper              | Temporary removable partial denture                | 250   | (Prosthodontics)        | True   | False    |
| Jaw Cyst Removal            | Excision of cysts in the jawbone                   | 900   | (Oral Surgery)          | True   | True     |
| Alveoloplasty               | Smoothing and shaping jawbone for dentures         | 450   | (Oral Surgery)          | True   | True     |
| Frenectomy                  | Removal of connective tissue in the mouth          | 350   | (Oral Surgery)          | True   | True     |
| Dental Bonding              | Resin applied to fix chipped or cracked teeth      | 180   | (Cosmetic Dentistry)    | True   | False    |
| Gum Contouring              | Laser reshaping of the gum line                    | 400   | (Cosmetic Dentistry)    | True   | True     |
| Smile Makeover Consultation | Comprehensive aesthetic treatment evaluation       | 100   | (Cosmetic Dentistry)    | True   | False    |
| Space Maintainer            | Prevents teeth shifting in children                | 150   | (Pediatric Dentistry)   | True   | True     |
| Pediatric Pulpectomy        | Complete root canal for baby teeth                 | 250   | (Pediatric Dentistry)   | True   | True     |
| Stainless Steel Crown       | Durable prefabricated cap for children's molars    | 180   | (Pediatric Dentistry)   | True   | False    |
| Custom Night Guard          | Splint for bruxism and teeth grinding              | 300   | (Preventive Dentistry)  | True   | True     |
| Oral Cancer Screening       | Thorough mucosal tissue evaluation                 | 50    | (Preventive Dentistry)  | True   | False    |
| Panoramic X-Ray             | Full mouth 2D diagnostic imaging                   | 70    | (Preventive Dentistry)  | True   | False    |
| Porcelain Inlay             | Custom filling fitted inside tooth cusps           | 400   | (Restorative Dentistry) | True   | True     |
| Porcelain Onlay             | Custom restoration covering one or more cusps      | 500   | (Restorative Dentistry) | True   | True     |
| Glass Ionomer Filling       | Fluoride-releasing cavity repair material          | 80    | (Restorative Dentistry) | True   | False    |
| All-on-4 Implants           | Full arch replacement anchored on four screws      | 12000 | (Implantology)          | True   | True     |
| Sinus Lift                  | Adding bone to the upper jaw prior to implants     | 1100  | (Implantology)          | True   | True     |
| Tooth Reimplantation        | Urgent stabilizing of an avulsed tooth             | 400   | (Dental Emergency)      | False  | True     |
| Palatal Expander            | Orthopedic device to widen the upper jaw           | 600   | (Orthodontics)          | True   | True     |
| Clear Retainer              | Transparent post-braces alignment tray             | 200   | (Orthodontics)          | True   | False    |
| Orthodontic Headgear        | Appliance for severe bite correction               | 800   | (Orthodontics)          | False  | True     |
| Internal Bleaching          | Whitening a discolored root canal tooth            | 300   | (Endodontics)           | True   | True     |
| Direct Pulp Capping         | Covering exposed nerve to avoid root canal         | 120   | (Endodontics)           | True   | False    |
| Apexification               | Inducing root closure in immature teeth            | 400   | (Endodontics)           | True   | True     |
| Gingivectomy                | Surgical removal of diseased gum tissue            | 450   | (Periodontics)          | True   | True     |
| Pocket Reduction Surgery    | Cleaning root surfaces and reducing gum pockets    | 750   | (Periodontics)          | True   | True     |
| Guided Tissue Regeneration  | Membrane placement for bone regrowth               | 850   | (Periodontics)          | True   | True     |
| Maryland Bridge             | Resin-bonded bridge attached to adjacent teeth     | 900   | (Prosthodontics)        | True   | True     |
| Cantilever Bridge           | Bridge supported by a single adjacent tooth        | 950   | (Prosthodontics)        | True   | True     |
| Overdenture                 | Denture supported by implants or retained roots    | 2500  | (Prosthodontics)        | True   | True     |
| Oral Lesion Biopsy          | Tissue sampling for pathology analysis             | 350   | (Oral Surgery)          | True   | True     |
| Ridge Augmentation          | Restoring bone contour after tooth extraction      | 650   | (Oral Surgery)          | True   | True     |
| Maxillary Antrostomy        | Surgical access to the maxillary sinus             | 1200  | (Oral Surgery)          | True   | True     |
| Enamel Microabrasion        | Removal of superficial tooth stains                | 150   | (Cosmetic Dentistry)    | True   | False    |
| Tooth Jewelry Placement     | Bonding a small gem to the tooth surface           | 80    | (Cosmetic Dentistry)    | False  | False    |
| Snap-On Smile               | Removable cosmetic arch worn over natural teeth    | 1100  | (Cosmetic Dentistry)    | True   | False    |
| Habit Breaking Appliance    | Device to stop thumb sucking or tongue thrusting   | 350   | (Pediatric Dentistry)   | True   | True     |
| Silver Diamine Fluoride     | Liquid treatment to stop tooth decay in kids       | 60    | (Pediatric Dentistry)   | True   | False    |
| Pediatric Tooth Extraction  | Removal of a loose or decayed primary tooth        | 90    | (Pediatric Dentistry)   | True   | False    |
| Sports Mouthguard           | Custom-fitted athletic mouth protector             | 200   | (Preventive Dentistry)  | True   | False    |
| CBCT Scan                   | 3D cone beam computed tomography imaging           | 150   | (Preventive Dentistry)  | True   | True     |
| Saliva Testing              | Diagnostic test for caries risk and dry mouth      | 75    | (Preventive Dentistry)  | True   | False    |
| Gold Crown                  | Traditional highly durable metal alloy cap         | 1100  | (Restorative Dentistry) | True   | True     |
| Temporary Crown             | Short-term acrylic cap while waiting for permanent | 150   | (Restorative Dentistry) | True   | False    |
| Pin-Retained Restoration    | Filling secured with metal pins for extra strength | 250   | (Restorative Dentistry) | True   | True     |
| Mini Dental Implants        | Narrow diameter implants for denture stabilization | 800   | (Implantology)          | True   | True     |
| Zygomatic Implants          | Long implants anchored directly in the cheekbone   | 3500  | (Implantology)          | True   | True     |
| Dry Socket Treatment        | Medication dressing for post-extraction pain       | 80    | (Dental Emergency)      | False  | True     |
| Interceptive Orthodontics   | Early phase treatment for mixed dentition          | 1200  | (Orthodontics)          | True   | True     |
| Damon Braces                | Self-ligating bracket system without elastics      | 3200  | (Orthodontics)          | True   | False    |
| Endodontic Surgery          | Micro-surgical repair of complex root issues       | 950   | (Endodontics)           | True   | True     |
| Vital Pulp Therapy          | Preserving the health of the dental pulp           | 220   | (Endodontics)           | True   | True     |
| Laser Periodontal Therapy   | Minimally invasive laser gum treatment             | 600   | (Periodontics)          | True   | True     |
| Tooth Splinting             | Stabilizing loose teeth with wire and resin        | 250   | (Periodontics)          | True   | True     |
| Cast Partial Denture        | Metal framework removable partial denture          | 850   | (Prosthodontics)        | True   | False    |
| Immediate Denture           | Denture placed immediately after extraction        | 1000  | (Prosthodontics)        | True   | False    |
| TMJ Arthrocentesis          | Minimally invasive jaw joint irrigation            | 700   | (Oral Surgery)          | True   | True     |
| Orthognathic Surgery        | Corrective jaw surgery for severe malocclusion     | 8000  | (Oral Surgery)          | True   | True     |
| Composite Veneers           | Direct resin bonding for aesthetic improvement     | 300   | (Cosmetic Dentistry)    | True   | False    |
| Gingival Depigmentation     | Laser removal of dark gum pigmentation             | 450   | (Cosmetic Dentistry)    | False  | True     |
| Nitrous Oxide Sedation      | Laughing gas for pediatric and anxious patients    | 100   | (Pediatric Dentistry)   | True   | False    |
| Pediatric Fluoride Varnish  | High concentration fluoride painted on teeth       | 45    | (Pediatric Dentistry)   | True   | False    |
| Desensitizing Treatment     | Application of agent for extreme tooth sensitivity | 50    | (Preventive Dentistry)  | True   | False    |
| Bitewing X-Rays             | Routine cavity detection radiographs               | 40    | (Preventive Dentistry)  | True   | False    |
| Core Buildup                | Structural foundation repair prior to crowning     | 200   | (Restorative Dentistry) | True   | True     |
| Inlay-Retained Bridge       | Conservative bridge anchored by adjacent inlays    | 1800  | (Restorative Dentistry) | True   | True     |
| Implant Maintenance         | Professional cleaning and check of dental implants | 120   | (Implantology)          | True   | False    |
| Lost Crown Recementation    | Urgent fixing of a dislodged permanent crown       | 80    | (Dental Emergency)      | True   | True     |


### Quote
| Valid Until | Patient ID          | Staff ID        | Items                      | Quantity | Discout | Teeth            |
| ----------- | ------------------- | --------------- | -------------------------- | -------- | ------- | ---------------- |
| 2026-10-02  | (Chiara Esposito)   | (Marco Bianchi) | (Implant Maintenance)      | 1        | 0       | []               |
|             |                     |                 | (Inlay-Retained Bridge)    | 2        | 0       | [33, 16]         |
| 2026-10-15  | (Martina Colombo)   | (Sofia Ricci)   | (Teeth Whitening)          | 1        | 10      | []               |
| 2026-10-18  | (Davide Marino)     | (Marco Bianchi) | (Dental Cleaning)          | 1        | 0       | []               |
|             |                     |                 | (Composite Filling)        | 1        | 0       | [14]             |
| 2026-10-20  | (Sara Russo)        | (Marco Bianchi) | (Clear Aligners)           | 1        | 5       | []               |
| 2026-10-22  | (Andrea Moretti)    | (Marco Bianchi) | (Root Canal Treatment)     | 1        | 0       | [26]             |
|             |                     |                 | (Zirconia Dental Crown)    | 1        | 0       | [26]             |
| 2026-10-25  | (Beatrice Barbieri) | (Marco Bianchi) | (Panoramic X-Ray)          | 1        | 0       | []               |
|             |                     |                 | (Simple Tooth Extraction)  | 2        | 0       | [38, 48]         |
| 2026-10-28  | (Simone Fontana)    | (Marco Bianchi) | (Single Dental Implant)    | 1        | 15      | [46]             |
| 2026-11-02  | (Silvia Rinaldi)    | (Marco Bianchi) | (Porcelain Veneers)        | 4        | 20      | [11, 12, 21, 22] |
| 2026-11-05  | (Giacomo Lombardi)  | (Sofia Ricci)   | (Full Dentures)            | 1        | 0       | []               |
| 2026-11-10  | (Federica Caruso)   | (Marco Bianchi) | (Dental Cleaning)          | 1        | 0       | []               |
|             |                     |                 | (Composite Filling)        | 2        | 0       | [15, 25]         |
| 2026-11-12  | (Stefano Ferrara)   | (Sofia Ricci)   | (Deep Scaling)             | 1        | 10      | []               |
| 2026-11-15  | (Alessia Mariani)   | (Marco Bianchi) | (Traditional Metal Braces) | 1        | 0       | []               |
| 2026-11-18  | (Nicola Bianco)     | (Sofia Ricci)   | (Ceramic Braces)           | 1        | 5       | []               |
| 2026-11-20  | (Francesca Gatti)   | (Marco Bianchi) | (Panoramic X-Ray)          | 1        | 0       | []               |
|             |                     |                 | (Wisdom Tooth Extraction)  | 1        | 0       | [28]             |
| 2026-11-25  | (Michele Santoro)   | (Marco Bianchi) | (Gum Graft Surgery)        | 1        | 10      | [41, 42]         |
| 2026-11-28  | (Paola Marini)      | (Sofia Ricci)   | (Dental Bonding)           | 1        | 0       | [11]             |
| 2026-12-02  | (Daniele Sala)      | (Sofia Ricci)   | (Custom Night Guard)       | 1        | 0       | []               |
| 2026-12-05  | (Laura Fiore)       | (Marco Bianchi) | (Apicoectomy)              | 1        | 0       | [22]             |
| 2026-12-10  | (Elisa Coppola)     | (Marco Bianchi) | (Dental Cleaning)          | 1        | 5       | []               |
|             |                     |                 | (Fluoride Application)     | 1        | 5       | []               |
| 2026-12-15  | (Paolo Galli)       | (Sofia Ricci)   | (Bone Grafting)            | 1        | 15      | [36]             |
|             |                     |                 | (Single Dental Implant)    | 1        | 15      | [36]             |
| 2026-12-20  | (Martina D'Amico)   | (Marco Bianchi) | (Teeth Whitening)          | 1        | 0       | []               |