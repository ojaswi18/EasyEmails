from django.shortcuts import render , redirect ,HttpResponse
from google_auth_oauthlib.flow import Flow
# from social_django.utils import load_strategy
from googleapiclient.discovery import build
import re
from google.oauth2.credentials import Credentials
import json
import base64
from django.http import JsonResponse
from googleapiclient.errors import HttpError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
from email.mime.base import MIMEBase
from email import encoders
import datetime
import pytz
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

scopes = ["https://mail.google.com/", "https://www.googleapis.com/auth/calendar.events"]


# Create your views here.

# This will store the server start time.


def home(request):
    flow = Flow.from_client_secrets_file(
        'MainApp/credentials.json', 
        scopes=scopes,
        redirect_uri="http://127.0.0.1:8000/auth/google/callback"
    )

    if 'code' not in request.GET:
        # Step 1: Generate authorization URL
        authorization_url, state = flow.authorization_url()
        print(state)
        print(authorization_url)
        # Store state in session
        request.session['oauth2_state'] = state
        return redirect(authorization_url)
    return render(request, 'home.html')


def google_callback(request):
    flow = Flow.from_client_secrets_file(
        'MainApp/credentials.json',
        scopes=scopes,
        redirect_uri="http://127.0.0.1:8000/auth/google/callback"
    )
    
    authorization_code = request.GET.get('code')
    state = request.session.get('oauth2_state') 
    
    if state is None or state != request.GET.get('state'):
        # Handle incorrect or missing state parameter
        return render(request, 'error.html', {'error': 'Invalid state parameter'})
    
    # Remove state from session
    del request.session['oauth2_state']
    
    flow.fetch_token(authorization_response=request.build_absolute_uri(),
                     code=authorization_code)
    credentials = flow.credentials
    
    refresh_token = credentials.refresh_token
   
    # Use the obtained credentials to make API calls
    service = build('gmail', 'v1', credentials=credentials)
    # Call the Gmail API to retrieve the user's emails
    results = service.users().messages().list(userId='me', maxResults=200).execute()
    emails = results.get('messages', [])
    first_email_detail = service.users().messages().get(userId='me', id=results['messages'][0]['id'], format='full').execute()
    headers = first_email_detail['payload']['headers']
    for header in headers:
        if header['name'] == 'Date':
         print(header['value'])
         break
    
    #google calendar api 
    service_calendar = build('calendar', 'v3', credentials=credentials)
    events_result = service_calendar.events().list(calendarId='primary', maxResults=10).execute()
    events = events_result.get('items', [])
    print("google calendar api done succ")
    
    for email in emails:   
      message = service.users().messages().get(userId='me', id=email['id'], format='full', fields='id, threadId, payload,snippet,labelIds').execute()
    
     
      label_ids = message['labelIds']
      email['star'] = 'STARRED' in label_ids
      email['read'] = 'UNREAD' not in label_ids
        
      payload = message["payload"] 
      if 'parts' in payload:
        #   print("parts")
          parts = payload['parts']
          for part in parts:
               if part['mimeType'] == 'text/html':
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                email['body'] = body
                break
               elif part['mimeType'] == 'text/plain':
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                email['body'] = body
                break
      elif 'body' in payload:
          data = payload['body']['data']
          body = base64.urlsafe_b64decode(data).decode('utf-8')
          email['body'] = body      
      elif "textPlain" in payload:  
          data = payload['textPlain']['data']
          body = base64.urlsafe_b64decode(data).decode('utf-8')
          email['body'] = body
      else:
          print("nothing") 
       
      
      headers = message['payload']['headers']
      
      for header in headers:
        if header['name'] == 'From':
            sender_info = header['value']
            match = re.match(r'^[^<]*', sender_info)
            if match:
                email['sender'] = match.group().strip()
                print(email['sender'])
            else:
                email['sender'] = sender_info
                print(email['sender'])
            email_match = re.search(r'<(.+?)>', sender_info)
            if email_match:
                email['sender_email'] = email_match.group(1)
                print(email['sender_email'])           
       
      for header in headers:
        if header['name'] == 'Date':
           if header['name'] == 'Date':
             timestamp = header['value']
             timestamp = timestamp.replace(' (UTC)', '')
             try:
                parsed_date = datetime.datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %z")
                email['full_date'] = parsed_date.strftime("%a, %d %b %Y %H:%M:%S %z")
                email['day_month'] = parsed_date.strftime("%d %B")
             except ValueError:
                email['full_date'] = "Unknown Date"
                email['day_month'] = "Unknown Date"
             break


      for header in headers:
          if header['name'] == 'Subject':
             email['subject'] = header['value']
             break  
          
    request.session['emails'] = emails
    request.session['events'] = events
    request.session['credentials'] = credentials.to_json()
    request.session['refresh_token'] = refresh_token
    request.session['data_refreshed'] = True

    
    context = {
        "emails":emails,
        "data_refreshed": True
    }
   
    return render(request, "gmail.html",context)

def sortedemails(request,slug):
    
    newslug=slug
    ee=request.session.get('emails', [])
    grouped_subjects = {
        'Group1': [],
        'Group2': [],
        'Group3': [],
        'Group4': [],
        'Group5': []
    }
       
    for email in ee:
      sender = email["sender"].lower()
      subject = email["subject"].lower()

      if any(keyword in sender for keyword in ['linkedin', 'jobs', 'mlh', 'intershala', 'internship']):
        grouped_subjects['Group1'].append(email)
      elif any(keyword in sender for keyword in ['bhawan', 'iit roorkee', 'acad office']):
        grouped_subjects['Group2'].append(email)
      elif any(keyword in subject for keyword in ['clubs', 'club', 'mdg', 'img', 'sds', 'dsg', 'thomso', 'cognisance', 'vlg', 'aries']):
        grouped_subjects['Group3'].append(email)
      else:
        grouped_subjects['Group4'].append(email)
       
    context={
        "groupdisplayed":grouped_subjects[newslug],
        "slug":newslug
    }
    
    return render(request, 'sortedemails.html',context)


def googlecalendar(request):
    # Retrieve the events from the session
    events = request.session.get('events', [])

    context = {
        "events": events
    }

    return render(request, "googlecalendar.html", context)

def addevent(request):
    return render(request,"addevent.html")

def compose(request):
    return render(request,"compose.html")

def sendEmail(request):
    if request.method == 'POST':
        sender = request.user.email
        recipient = request.POST.get('recipient')
        cc = request.POST.get('cc')
        bcc = request.POST.get('bcc')
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        attachment = request.FILES.get('attachment')
        
        refresh_token = request.session.get('refresh_token')
        credentials_data = request.session.get('credentials')
        credentials_dict = json.loads(credentials_data)
        if 'refresh_token' not in credentials_dict:
            print("enetred refresh token if")
            credentials_dict['refresh_token'] = refresh_token

        credentials = Credentials.from_authorized_user_info(credentials_dict)
        print("done till cred")
        try:
            service = build('gmail', 'v1', credentials=credentials)
            print('service done')
            message = MIMEMultipart()
            message['From'] = sender
            message['To'] = recipient
            message['Cc'] = cc
            message['Bcc'] = bcc
            message['Subject'] = subject
            print("all message part done")
            # Attach the email body
            body = MIMEText(content, 'plain')
            message.attach(body)
            print("message body done")
            # Attach the file if provided
            if attachment:
                filename = attachment.name
                content_type, encoding = mimetypes.guess_type(filename)

                if content_type is None or encoding is not None:
                    content_type = 'application/octet-stream'
                print("before main type")
                main_type, sub_type = content_type.split('/', 1)
                print("after main type")
                attachment_part = MIMEBase(main_type, sub_type)
                attachment_part.set_payload(attachment.read())
                print("before")
                encoders.encode_base64(attachment_part)
                attachment_part.add_header('Content-Disposition', 'attachment', filename=filename)
                message.attach(attachment_part)
                print("attachment done successfully")
                
            # Convert the message to a raw string
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            print("raw message done succ")

            # # Send the email
            service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            return JsonResponse({'success': True, 'message': 'Email sent successfully.'}) 

        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Error sending email: ' + str(e)})


def forward(request, email_id):
    print("inside forward function")
    emails = request.session.get('emails', [])
    if request.method == "POST":
           data = json.loads(request.body)
           email_id = data.get('emailId')
           recipient = data.get('recipientEmail')
           print(recipient)  
    attachment = None 
    email_to_forward = None
    response_data = {}  # This dictionary will hold the response data

    for email in emails:
        if email['id'] == email_id:
            email_to_forward = email
            break

    if email_to_forward is not None: 
        subject = 'Fwd: ' + email_to_forward['subject']
        content = email_to_forward['body']
        print(content)

        refresh_token = request.session.get('refresh_token')
        credentials_data = request.session.get('credentials')
        credentials_dict = json.loads(credentials_data)
        if 'refresh_token' not in credentials_dict:
            credentials_dict['refresh_token'] = refresh_token

        credentials = Credentials.from_authorized_user_info(credentials_dict)

        try:
            service = build('gmail', 'v1', credentials=credentials)
            message = MIMEMultipart()
            message['To'] = recipient
            message['Subject'] = subject

            # Attach the email body
            body = MIMEText(content, 'plain')
            message.attach(body)

            # Convert the message to a raw string
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send the email
            service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            response_data['status'] = 'success'
            response_data['message'] = 'Email forwarded successfully.'

        except Exception as e:
            response_data['status'] = 'error'
            response_data['message'] = f'Error forwarding email: {str(e)}'

    else:
        response_data['status'] = 'error'
        response_data['message'] = 'The specified email was not found.'

    return JsonResponse(response_data)



def reply(request, email_id):
    print("inside reply")
    emails = request.session.get('emails', [])
    
    email_to_reply = None
    for email in emails:
        if email['id'] == email_id:
            email_to_reply = email
            break

    if email_to_reply is not None:
        recipient = email_to_reply['sender_email'] 
        print(recipient)
        subject = 'Re: ' + email_to_reply['subject']
        if request.method == "POST":
           data = json.loads(request.body)
           email_id = data.get('emailId')
           reply_text = data.get('replyText')
        content = reply_text  
    
        refresh_token = request.session.get('refresh_token')
        credentials_data = request.session.get('credentials')
        credentials_dict = json.loads(credentials_data)
        if 'refresh_token' not in credentials_dict:
            credentials_dict['refresh_token'] = refresh_token

        credentials = Credentials.from_authorized_user_info(credentials_dict)
        print("after cred and before try")
        try:
            service = build('gmail', 'v1', credentials=credentials)
            message = MIMEMultipart()
            message['To'] = recipient
            message['Subject'] = subject
            thread_id = email_to_reply.get('threadId')
            print(thread_id)
        
            body = MIMEText(content, 'plain')
            message.attach(body)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            # service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            if thread_id:
                service.users().messages().send(userId='me', body={'raw': raw_message, 'threadId': thread_id}).execute()
            else:
                service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            messages.success(request, 'Email replied successfully.')
            return JsonResponse({'status': 'success', 'message': 'Email replied successfully.'})

        except Exception as e:
            messages.error(request, f'Error replying to email: {str(e)}')
            return JsonResponse({'status': 'error', 'message': f'Error replying to email: {str(e)}'})

    else:
        messages.error(request, 'The specified email was not found.')
        return JsonResponse({'status': 'error', 'message': 'The specified email was not found.'})


def create_event(request):
    refresh_token = request.session.get('refresh_token')
    if request.method == 'POST':
        title = request.POST.get('title')
        start = request.POST.get('start')
        end = request.POST.get('end')
        location = request.POST.get('location')
        description = request.POST.get('description')
        reminders = request.POST.get('reminders')
        attendees = request.POST.get('attendees')
        
        print("before retriving service object")
        
        credentials_data = request.session.get('credentials')
        credentials_dict = json.loads(credentials_data)
        if 'refresh_token' not in credentials_dict:
            print("enetred refresh token if")
            credentials_dict['refresh_token'] = refresh_token

        credentials = Credentials.from_authorized_user_info(credentials_dict)
        service_calendar = build('calendar', 'v3', credentials=credentials)
        print("after service,code succ till now for creating event")
       
        event_start = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M').isoformat()
        event_end = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M').isoformat()
        print("format of date and time done")
        
        timezone = pytz.timezone('Asia/Kolkata')  # Replace with your desired timezone
        event_start = timezone.localize(datetime.datetime.fromisoformat(event_start))
        event_end = timezone.localize(datetime.datetime.fromisoformat(event_end))
        
    event = {
    'summary': title,
    'location': location,
    'description': description,
    'start': {
        'dateTime': event_start.isoformat(),
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': event_end.isoformat(),
        'timeZone': 'Asia/Kolkata',
    },
    'attendees': [{'email': attendee} for attendee in attendees.split(',')],
    # 'reminders': {
    #     'useDefault': False,
    #     'overrides': [{'method': 'popup', 'minutes': int(reminder)} for reminder in reminders.split(',')],
    # },
}

    event = service_calendar.events().insert(calendarId='primary', body=event).execute()
    print("Event executed")
        
    return render(request,"home.html")    


def emailbody(request):
    print("inside emailbody function")
    
    emailbody_id = request.GET.get('id')
    
    emails = request.session.get('emails', [])
    
    matching_email = None
    for email in emails:
        if email['id'] == emailbody_id:
            matching_email = email
            break
        
    return render(request, 'emailbody.html', {'email': matching_email})

def get_processed_emails(request):
    emails = request.session.get('emails', [])
    data_refreshed = request.session.get('data_refreshed', False)
    
    # Remove it from the session after you've accessed it
    if data_refreshed:
        del request.session['data_refreshed']

    response_data = {
        "emails": emails,
        "data_refreshed": data_refreshed
    }
    
    return JsonResponse(response_data)


def starEmail(request,email_id):
    print("enetered in star ")
    refresh_token = request.session.get('refresh_token')
    credentials_data = request.session.get('credentials')
    credentials_dict = json.loads(credentials_data)
    if 'refresh_token' not in credentials_dict:
        print("enetred refresh token if")
        credentials_dict['refresh_token'] = refresh_token
    print("before cred")
    creds= Credentials.from_authorized_user_info(credentials_dict)
    print("before service")
    service = build('gmail', 'v1', credentials=creds)
    print("before message")
    message = service.users().messages().get(
        userId='me',
        id=email_id,
        format='full',
        fields='labelIds'
    ).execute()
    print("after message")
    original_labels = message['labelIds']
    print(original_labels)
    isStarred=False
    if 'STARRED' not in original_labels:
        print("not in original_labels")
        # Modify the email to add the 'STARRED' label
        print("before modified")
        modified_message = service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'addLabelIds': ['STARRED']}
        ).execute()
        isStarred=True
        print("after modified")
        
    else:
        print("in original_labels")
        # Modify the email to remove the 'STARRED' label
        print("before modified")
        modified_message = service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'removeLabelIds': ['STARRED']}
        ).execute()
        print("before modified")
        
    if isStarred:
        message = 'Email starred'
    else:
        message = 'Email unstarred'
        
    return JsonResponse({'message': message})


def markEmailAsRead(request):
    print("inside markasread")
    email_id = request.GET.get('id')
    print(email_id)
    refresh_token = request.session.get('refresh_token')
    credentials_data = request.session.get('credentials')
    credentials_dict = json.loads(credentials_data)

    if 'refresh_token' not in credentials_dict:
        credentials_dict['refresh_token'] = refresh_token

    creds = Credentials.from_authorized_user_info(credentials_dict)
    service = build('gmail', 'v1', credentials=creds)

    # Get the original labels of the email
    message = service.users().messages().get(
        userId='me',
        id=email_id,
        format='full',
        fields='labelIds'
    ).execute()

    original_labels = message['labelIds']

    isRead = False

    # If the email does not have the 'UNREAD' label, it's already read
    if 'UNREAD' in original_labels:
        # Modify the email to remove the 'UNREAD' label
        modified_message = service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        isRead = True
    else:
        # Modify the email to add the 'UNREAD' label
        modified_message = service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'addLabelIds': ['UNREAD']}
        ).execute()
        
    if isRead:
        messages.success(request, 'Email marked as read.')
        return JsonResponse({'status': 'success', 'message': 'Email marked as read.'})
    else:
        messages.error(request, 'Failed to mark email as read.')
        return JsonResponse({'status': 'error', 'message': 'Failed to mark email as read.'})



def delete_email(request, email_id):
    print("inside delete email def in vews")
    print(email_id)
    refresh_token = request.session.get('refresh_token')
    print(refresh_token)
    credentials_data = request.session.get('credentials')
    credentials_dict = json.loads(credentials_data)
    if 'refresh_token' not in credentials_dict:
        print("enetred refresh token if")
        credentials_dict['refresh_token'] = refresh_token
    print("before cred")
    creds= Credentials.from_authorized_user_info(credentials_dict)
    print(creds)
    service = build('gmail', 'v1', credentials=creds)
    print(service )
    print(email_id)
    try:
        service.users().messages().delete(userId='me', id=email_id).execute()
        print("inside try")
        return JsonResponse({'message': 'Email deleted successfully'})
    except HttpError as e:
        error_message = f"An error occurred: {e}"
        return JsonResponse({'message': error_message}, status=500)
    


@csrf_exempt
def block_sender(request):

    # Check for POST method.
    if request.method != "POST":
        return JsonResponse({"error": "POST method required."}, status=400)

    # Parse the POST request's body to get sender_email.
    body_unicode = request.body.decode('utf-8')
    body_data = json.loads(body_unicode)
    sender_email = body_data.get('sender_email')
    
    if not sender_email:
        return JsonResponse({"error": "Sender email is required"}, status=400)

    # Get credentials from session.
    refresh_token = request.session.get('refresh_token')
    credentials_data = request.session.get('credentials')
    
    if not credentials_data:
        return JsonResponse({"error": "User is not authenticated with Gmail."}, status=401)

    credentials_dict = json.loads(credentials_data)
    if 'refresh_token' not in credentials_dict:
        credentials_dict['refresh_token'] = refresh_token

    creds = Credentials.from_authorized_user_info(credentials_dict)
    service = build('gmail', 'v1', credentials=creds)

    # Retrieve or create "Blocked Emails" label ID
    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        blocked_emails_label_id = None

        for label in labels:
            if label['name'] == 'Blocked Emails':
                blocked_emails_label_id = label['id']
                break

        if not blocked_emails_label_id:
            # If label doesn't exist, create it.
            label_body = {
                'name': 'Blocked Emails',
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            created_label = service.users().labels().create(userId='me', body=label_body).execute()
            blocked_emails_label_id = created_label['id']

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    # Create a filter to move future emails from the blocked sender to "Blocked Emails".
    filter_body = {
        "criteria": {
            "from": sender_email
        },
        "action": {
            "addLabelIds": [blocked_emails_label_id],  # Use the label ID here
            "removeLabelIds": ["INBOX"]
        }
    }

    # ... [the previous part of the block_sender function]

    try:
        service.users().settings().filters().create(userId='me', body=filter_body).execute()
        print("try done")
        return JsonResponse({"message": "Sender blocked successfully. Future emails from this sender will be labeled as 'Blocked Emails'."}, status=200)
    
    except Exception as e:
        error_message = str(e)
        print(error_message)
        
        if "Filter already exists" in error_message:
            print(str(e))
            return JsonResponse({"message": "Sender already bocked."}, status=409)  # 409 Conflict
        
        return JsonResponse({"error": error_message}, status=500)


    







   

