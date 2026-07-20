/* Backend for 230redstreet.com.
   Receives audition submissions, appends them to this spreadsheet, and emails Ryan.
   The reference copy lives in the site repo; this code only runs once pasted into
   the Apps Script editor and deployed. */

var SHEET_NAME = 'Submissions';
var NOTIFY_EMAIL = 'ryan@ryanclayton.media';

/* Must stay identical to the form field names in index.html.
   tools/validate_site.py fails the build if they drift apart. */
var FIELDS = ['name', 'email', 'phone', 'location', 'role', 'physical',
              'tape_link', 'headshot', 'reel', 'availability', 'notes'];

function doGet() {
  // Lets you confirm the deployment is live by opening the /exec URL in a browser.
  return ContentService.createTextOutput('230 Red Street audition endpoint is live.');
}

function doPost(e) {
  try {
    var p = (e && e.parameter) || {};

    // Honeypot. Real people never see this field, so anything in it is a bot.
    // Return OK so the bot treats it as success and does not retry.
    if (p['bot-field']) {
      return ContentService.createTextOutput('OK');
    }

    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
    if (!sheet) {
      throw new Error('Sheet named "' + SHEET_NAME + '" not found');
    }

    var row = [new Date()];
    for (var i = 0; i < FIELDS.length; i++) {
      row.push(p[FIELDS[i]] || '');
    }
    row.push('New'); // Status
    row.push('');    // Review notes
    sheet.appendRow(row);

    MailApp.sendEmail({
      to: NOTIFY_EMAIL,
      subject: '230 Red Street audition — ' + (p.role || 'unspecified role') +
               ' — ' + (p.name || 'unnamed'),
      body: [
        'Name: ' + (p.name || ''),
        'Role: ' + (p.role || ''),
        'Location: ' + (p.location || ''),
        'Height / build / hair: ' + (p.physical || ''),
        '',
        'TAPE: ' + (p.tape_link || ''),
        'Headshot: ' + (p.headshot || ''),
        'Reel: ' + (p.reel || ''),
        '',
        'Email: ' + (p.email || ''),
        'Phone: ' + (p.phone || ''),
        'Availability: ' + (p.availability || ''),
        'Notes: ' + (p.notes || '')
      ].join('\n')
    });

    return ContentService.createTextOutput('OK');
  } catch (err) {
    // Surfaces in the Apps Script editor under Executions.
    console.error(err);
    return ContentService.createTextOutput('ERROR: ' + err.message);
  }
}
