function toggleIcon(emailId) {
    console.log("inside toggle function");
    console.log("testing immediate log");
    console.log("Email ID:", emailId);
    var starIcon1 = document.getElementById('star-icon1-' + emailId);
    var starIcon2 = document.getElementById('star-icon2-' + emailId);
    console.log("StarIcon1:", starIcon1);
    console.log("StarIcon2:", starIcon2);
    var isStarred = starIcon2.style.display === 'none';
    console.log("Is Starred:", isStarred);

    // Toggle the star icons' display.
    starIcon1.style.display = isStarred ? 'none' : 'inline';
    starIcon2.style.display = isStarred ? 'inline' : 'none';
    fetch(`/starEmail/${emailId}/`)
    .then(response => {
        console.log("inside fetch");
        if (response.ok) {
            if (isStarred) {
                alert('Email has been starred.');
            } else {
                alert('Email has been unstarred.');
            }
        } else {
            throw new Error('Failed to star/unstar email');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
    localStorage.setItem('email_star_status_' + emailId, isStarred);
    console.log("afer localstorage");
   
    updateStarStatusFromStorage(emailId);    
}

window.addEventListener("pageshow", function(event) {
    console.log("inside windows pageshow function");
    if (event.persisted || (typeof window.performance != "undefined" && window.performance.navigation.type === 2)) {
        // Page was loaded from cache
        var emailIds = [...document.querySelectorAll('.star-button')].map(btn => btn.id.replace('star-button-', ''));
        emailIds.forEach(id => updateStarStatusFromStorage(id));
    }
});


let originalEmailStatuses = {}; // to hold the backend data

document.addEventListener('DOMContentLoaded', function() {
    console.log("inside document listener");

    fetch('/getProcessedEmails')
    .then(response => response.json())
    .then(data => {
        if(data.data_refreshed) {
            clearEmailStarStatusesFromLocalStorage();
        }
        const emails = data.emails || [];
        originalEmailStatuses = emails.reduce((acc, email) => {
            acc[email.id] = email.star;
            return acc;
        }, {});
        
        var emailIds = [...document.querySelectorAll('.star-button')].map(btn => btn.id.replace('star-button-', ''));
        emailIds.forEach(id => updateStarStatusFromStorage(id));
    });
});

function clearEmailStarStatusesFromLocalStorage() {
    Object.keys(localStorage).forEach(key => {
        if(key.startsWith('email_star_status_')) {
            localStorage.removeItem(key);
        }
    });
}


function clearEmailStarStatusesFromLocalStorage() {
    Object.keys(localStorage).forEach(key => {
        if(key.startsWith('email_star_status_')) {
            localStorage.removeItem(key);
        }
    });
}

function updateStarStatusFromStorage(emailId) {
    console.log("inside update status function");
    var isStarred;
    
    // Check local storage first
    if(localStorage.getItem('email_star_status_' + emailId)) {
        isStarred = localStorage.getItem('email_star_status_' + emailId) === 'true';
    } else {
        // Fall back to original backend data
        isStarred = originalEmailStatuses[emailId];
    }
    
    var starIcon1 = document.getElementById('star-icon1-' + emailId);
    var starIcon2 = document.getElementById('star-icon2-' + emailId);
    
    if (starIcon1 && starIcon2) {
        starIcon1.style.display = isStarred ? 'none' : 'inline';
        starIcon2.style.display = isStarred ? 'inline' : 'none';
    } else {
        console.warn(`Star icons for email ID ${emailId} not found.`);
    }
}

