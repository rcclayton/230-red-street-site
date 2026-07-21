/* Backend for 230redstreet.com.
   Receives audition AND crew submissions, appends them to the matching tab of
   this spreadsheet, and emails Ryan. The reference copy lives in the site repo;
   this code only runs once pasted into the Apps Script editor and deployed.

   IMPORTANT: after editing this file you must re-deploy as a NEW VERSION in the
   Apps Script editor. A stale deployment drops submissions while the page still
   shows a success panel. */

var SHEET_NAME = 'Submissions';
var CREW_SHEET_NAME = 'Crew';
var NOTIFY_EMAIL = 'ryan@ryanclayton.media';

/* Must stay identical to the form field names in index.html.
   tools/validate_site.py fails the build if they drift apart. */
var FIELDS = ['name', 'email', 'phone', 'location', 'role', 'physical',
              'tape_link', 'headshot', 'reel', 'availability', 'notes'];

var CREW_FIELDS = ['name', 'email', 'phone', 'location', 'position',
                   'experience', 'nights', 'own_gear', 'links', 'notes'];

function doGet() {
  // Lets you confirm the deployment is live by opening the /exec URL in a browser.
  return ContentService.createTextOutput('230 Red Street endpoint is live (auditions + crew).');
}

function doPost(e) {
  try {
    var p = (e && e.parameter) || {};

    // Honeypot. Real people never see this field, so anything in it is a bot.
    // Return OK so the bot treats it as success and does not retry.
    if (p['bot-field']) {
      return ContentService.createTextOutput('OK');
    }

    // Anything that is not explicitly crew is treated as an audition, so the
    // existing form keeps working unchanged even without a form_type param.
    if (p.form_type === 'crew') {
      handleCrew(p);
    } else {
      handleAudition(p);
    }

    return ContentService.createTextOutput('OK');
  } catch (err) {
    // Surfaces in the Apps Script editor under Executions.
    console.error(err);
    return ContentService.createTextOutput('ERROR: ' + err.message);
  }
}

function appendRow(sheetName, fields, p) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  if (!sheet) {
    throw new Error('Sheet named "' + sheetName + '" not found');
  }
  var row = [new Date()];
  for (var i = 0; i < fields.length; i++) {
    row.push(p[fields[i]] || '');
  }
  row.push('New'); // Status
  row.push('');    // Review notes
  sheet.appendRow(row);
}

function handleAudition(p) {
  appendRow(SHEET_NAME, FIELDS, p);

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
}

function handleCrew(p) {
  appendRow(CREW_SHEET_NAME, CREW_FIELDS, p);

  MailApp.sendEmail({
    to: NOTIFY_EMAIL,
    subject: '230 Red Street crew — ' + (p.position || 'unspecified position') +
             ' — ' + (p.name || 'unnamed'),
    body: [
      'Name: ' + (p.name || ''),
      'Position: ' + (p.position || ''),
      'Location: ' + (p.location || ''),
      'Nights available: ' + (p.nights || ''),
      '',
      'Experience: ' + (p.experience || ''),
      'Own gear: ' + (p.own_gear || ''),
      'Links: ' + (p.links || ''),
      '',
      'Email: ' + (p.email || ''),
      'Phone: ' + (p.phone || ''),
      'Notes: ' + (p.notes || '')
    ].join('\n')
  });
}
