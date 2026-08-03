function doPost(e) {
  try {
    // Parse the incoming JSON payload
    // Note: When using mode: 'no-cors' from the frontend, the payload is often sent as raw postData
    let data;
    if (e.postData && e.postData.contents) {
      data = JSON.parse(e.postData.contents);
    } else {
      data = JSON.parse(e.parameter.data || "{}");
    }

    const leads = data.leads;
    const subject = data.subject || "Partnership Inquiry";

    if (!leads || !Array.isArray(leads)) {
      return ContentService.createTextOutput(JSON.stringify({
        status: 'error',
        message: 'Invalid payload. "leads" array is required.'
      })).setMimeType(ContentService.MimeType.JSON);
    }

    let emailsSent = 0;

    // Iterate through leads and send emails
    leads.forEach(lead => {
      if (lead.email) {
        // Construct a personalized email body
        const firstName = lead.name ? lead.name.split(' ')[0] : 'there';
        const body = `Hi ${firstName},\n\n` +
          `I noticed your work as ${lead.title || 'a professional'} at ${lead.company || 'your company'} and wanted to reach out regarding potential product supply opportunities.\n\n` +
          `Would you be generally open to reviewing a catalog?\n\n` +
          `Best regards,`;

        // Send the email using the connected Gmail account
        GmailApp.sendEmail(lead.email, subject, body);
        emailsSent++;
      }
    });

    // Return success response
    return ContentService.createTextOutput(JSON.stringify({
      status: 'success',
      message: `Successfully sent ${emailsSent} emails.`
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    // Return error response
    return ContentService.createTextOutput(JSON.stringify({
      status: 'error',
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

// Support for CORS preflight (OPTIONS request) if needed
function doOptions(e) {
  return ContentService.createTextOutput("")
    .setMimeType(ContentService.MimeType.TEXT)
    .setHeaders({
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type"
    });
}
