from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    # Print "Created user {username}" if create was successful.
    if len(tokens) != 3:
        print("Failed to create patient.")
        return

    username = tokens[1]
    password = tokens[2]
    if not strongPassword(password):
        print("Password is not strong, please try a strong password")
        return

    # If the username is already taken, print “Username taken, try again!”.
    if username_exists_patient(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)
    
    # create the patient
    patient = Patient(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    if not strongPassword(password):
        print("Password is not strong, please try a strong password")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def login_patient(tokens):
    # If a user is already logged in in the current session, you need to log out first before logging in again. In this case, print “User already logged in.”.
    global current_patient
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # For all other errors, print "Login failed.". Otherwise, print "Logged in as: [username]".
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if patient is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_patient = patient


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    
    if len(tokens) != 2:
        print("Please try again!")
        return
    
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    try:
        get_available_caregivers = "SELECT Username FROM Availabilities WHERE Time = %s ORDER BY Username"
        time = tokens[1]
        cursor.execute(get_available_caregivers, time)
        print("Caregivers:")
        for username in cursor:
            print(username[0])
    
        get_vaccines = "SELECT Name, Doses FROM Vaccines"
        cursor.execute(get_vaccines)
        print("\nVaccines:")
        for vaccines in cursor:
            print(vaccines[0] + ": " + str(vaccines[1]) + " doses")
    except:
        print("Please try again!")
    finally:
        cm.close_connection()

def reserve(tokens):
    if current_patient is None and current_caregiver is None:
        print("Please login first!")
        return

    if current_caregiver is not None:
        print("Please login as a patient!")

    if len(tokens) != 3:
        print("Please try again!")
    
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()
    
    time = tokens[1]
    vaccine = tokens[2]

    try:
        get_available_caregivers = "SELECT Username FROM Availabilities WHERE Time = %s ORDER BY Username"
        cursor.execute(get_available_caregivers, time)
        caregivers = cursor.fetchall()
        if not caregivers:
            print("No Caregiver is available!")
            return
    
        get_vaccines = "SELECT Doses FROM Vaccines WHERE Name = %s"
        cursor.execute(get_vaccines, vaccine)
        doses = cursor.fetchall()[0][0]
        if doses == 0:
            print("Not enough available doses!")
            return
        
        appointed_caregiver = caregivers[0][0]
        add_caregivers = "INSERT INTO Reservations VALUES (%s, %s, %s, %s)"
        cursor.execute(add_caregivers, (current_patient.username, appointed_caregiver, vaccine, time))
        conn.commit()        
        appointmentID = cursor.lastrowid

        delete_caregiver = "DELETE FROM Availabilities WHERE Username = %s"
        cursor.execute(delete_caregiver, appointed_caregiver)
        conn.commit()
    
        update_doses = "UPDATE Vaccines SET Doses = %d WHERE Name = %s"
        cursor.execute(update_doses, (int(doses) - 1, vaccine))
        conn.commit()

        print("Appointment ID: " + str(appointmentID) + ", Caregiver username: " + appointed_caregiver);
    
    except:
        print("Please try again!")
    finally:
        cm.close_connection()

def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")


def cancel(tokens):
    if current_patient is None:
        print("Please login first!")
        return

    if len(tokens) != 2:
        print("Please try again!")
        return

    try:
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)
        cancel_id = tokens[1]

        # Check 1: check that the user's desired appointment id is actually in their own appointments
        get_appointment = "SELECT Appointment_id, Vaccine_name, Time, Patient_name, Caregiver_name FROM Appointments WHERE Appointment_id = %d"
        cursor.execute(get_appointment, cancel_id)
        appointment = cursor.fetchone()
        valid_appointment = False
        if current_patient is not None:
            if appointment['Patient_name'] == current_patient.username:
                valid_appointment = True
            else:
                print("Could not find appointment with id:", cancel_id)
        elif current_caregiver is not None:
            if appointment['Caregiver_name'] == current_caregiver.username:
                valid_appointment = True
            else:
                print("Could not find appointment with id:", cancel_id)

        # If valid appointment id, then delete that appointment while replenishing the respective vaccine supply (+1)
        if valid_appointment:
            delete_appointment = "DELETE FROM Appointments WHERE Appointment_id = %d"
            vaccine = Vaccine(appointment["Vaccine_name"], None).get()
            vaccine.increase_available_doses(1)  # Need this to replenish 1 more vaccine if cancel is successful
            cursor.execute(delete_appointment, cancel_id)
            conn.commit()
            print("Appointment successfully cancelled.")
            if current_patient is not None:  # If a patient canceled that appointment, add the availability back to caregiver
                appointment_date = appointment['Time']
                caregiver = appointment['Caregiver_name']
                cursor.execute("INSERT INTO Availabilities VALUES (%d, %d)", (appointment_date, caregiver))
                conn.commit()
        else:
            print("Could not find appointment with id:", cancel_id)
    except pymssql.Error as e:
        print("Failed to retrieve appointment information")
        print("DBError:", e)
    except Exception as e:
        print("Could not find appointment with id:", cancel_id)
    finally:
        cm.close_connection()


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    try:
        if current_caregiver is not None:
            caregiver_reservation = "SELECT AppointmentID, VaccineName, Time, PUsername FROM Reservations WHERE CUsername = %s ORDER BY AppointmentID"
            cursor.execute(caregiver_reservation, current_caregiver.username)
            for info in cursor:
                print("Appointment ID: " + str(info['AppointmentID']) + ", Vaccine Name: " + info['VaccineName'] + ", Date: " + str(info['Time']) + ", Patient Name: " + info['PUsername'])
    
        if current_patient is not None:
            patient_reservation = "SELECT AppointmentID, VaccineName, Time, CUsername FROM Reservations WHERE PUsername = %s ORDER BY AppointmentID"
            cursor.execute(patient_reservation, current_patient.username)
            for info in cursor:
                print("Appointment ID: " + str(info['AppointmentID']) + ", Vaccine Name: " + info['VaccineName'] + ", Date: " + str(info['Time']) + ", Caregiver Name: " + info['CUsername'])

    except:
        print("Please try again!")
    finally:
        cm.close_connection()


def logout(tokens):
    global current_patient
    global current_caregiver
    
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    try:  
        current_patient = None
        current_caregiver = None
        print("Successfully logged out!")
    except:
        print("Please try again!")


def strongPassword(password):
    specialCharacters = ["!", "@", "#", "?"]
    errors = []

    containsSpecial = any(char in specialCharacters for char in password)
    containsLetter = any(char.isalpha() for char in password)
    containsNumber = any(char.isdigit() for char in password)

    if len(password) < 8:
        errors.append("At least 8 characters.")
    if not (containsLetter and containsNumber):
        errors.append("A mixture of letters and numbers.")
    if not containsSpecial:
        errors.append("Inclusion of at least one special character, from '!', '@', '#', '?'.")  # Use straight double quotes here.

    if len(errors) == 0:
        return True
    else:
        for error in errors:
            print(error)
        return False


def start():
    stop = False
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> Quit")
    print()
    while not stop:
        response = ""
        print("> ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break

        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == "cancel":
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
