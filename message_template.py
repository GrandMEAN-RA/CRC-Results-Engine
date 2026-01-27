


def email_template(student_name, firstname, surname, session, category, halfterm_var):

    if category == "Students":
        if halfterm_var:
            return (f"Dear {firstname},\n the entire management and staff of Christ The Redeemer's College-Christhill warmly appreciate your "
            "efforts towards achieving good academic performance this half term. We ubiquitously encourage you to push harder next half term for better "
            f"end of term results. \n Please, find attached your results for {session} half term.")
        else:
            return (f"Dear {firstname},\n the entire management and staff of Christ The Redeemer's College-Christhill warmly appreciate "
            "your efforts towards achieving good academic performance this term. We ubiquitously encourage you to push harder next term for better "
            f"results. \n Please, find attached your results for {session} academic session") 
    else:
        if halfterm_var:
            print("hereeeee!!!")
            return (f"Dear Mr. & Mrs. {surname}, the entire management and staff of Christ The Redeemer's College-Christhill warmly appreciate "
            f"{firstname}'s efforts towards achieving good academic performance this half term. We ubiquitously appreciate you also for your investments "
            "financially, and commitment to responding promptly to the school's demands to this regards. We believe the end of term results will be better "
            f"than this. \n Please, find attached {firstname}'s results for {session} half term.")
        else:
            return (f"Dear Mr. & Mrs. {surname}, the entire management and staff of Christ The Redeemer's College-Christhill warmly "
            f"appreciate {firstname}'s efforts towards achieving good academic performance this term. We ubiquitously appreciate you also for your "
            "investments financially, and commitment to responding promptly to the school's demands to this regards. We believe next term will be better "
            f"than this. \n Please, find attached {firstname}'s results for {session} academic session")
        
    print("Returning email body text template")
    

def whatsapp_template(student_name, firstname, surname, session, halfterm_var, msg_text, media_url):

    if halfterm_var:
        if msg_text:
            return msg_text + " " + f"\n Please, download {session} result document for {student_name} here: {media_url}"
        else:
            return (f"Dear Mr. & Mrs. {surname}, the entire management and staff of Christ The Redeemer's College-Christhill warmly appreciate {firstname}'s "
            "efforts towards achieving good academic performance this half term. We ubiquitously appreciate you also for your investments financially, and "
            "commitment to responding promptly to the school's demands to this regards. We believe the end of term results will be better than this. \n Please, "
            f"download {session} result document for {firstname} here: {media_url}")
    else:
        if msg_text:
            return msg_text + " " + f"\n Please, download {session} result document for {student_name} here: {media_url}"
        else:
            return (f"Dear Mr. & Mrs. {surname}, the entire management and staff of Christ The Redeemer's College-Christhill warmly appreciate {firstname}'s "
                    "efforts towards achieving good academic performance this term. We ubiquitously appreciate you also for your investments financially, and "
                    "commitment to responding promptly to the school's demands to this regards. We believe next term will be better than this. \n Please, "
                    f"download {session} result document for {firstname} here: {media_url}")

    print("Returning whatsapp body text templates")       

    





