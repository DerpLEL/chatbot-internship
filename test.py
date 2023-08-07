import numpy as np

leave_application_form = {
            'start_date': '',
            'end_date': '',
            'duration': 0,
            'note': '',
            'periodType': -1,
            'reviewUser': 0,
        }
        
leave_application_form_str = leave_application_form.replace("'", "''")
print(str(leave_application_form_str))
