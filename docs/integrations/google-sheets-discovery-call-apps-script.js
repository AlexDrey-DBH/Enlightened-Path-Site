const DISCOVERY_SHEET_NAME = "Discovery Calls";
const NEWSLETTER_SHEET_NAME = "Newsletter Opt Ins";

function doGet() {
  return jsonResponse_({
    ok: true,
    message: "Enlightened Path Healing discovery call endpoint is running."
  });
}

function doPost(event) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);

  try {
    const payload = parsePayload_(event);
    const email = String(payload.email || "").trim();

    if (!email || !/@/.test(email)) {
      return jsonResponse_({ ok: false, error: "A valid email address is required." });
    }

    const discoverySheet = getSheet_(DISCOVERY_SHEET_NAME, [
      "Submitted At",
      "Email",
      "Newsletter Opt-In",
      "Source",
      "Page URL",
      "Page Title",
      "User Agent"
    ]);

    discoverySheet.appendRow([
      payload.submittedAt || new Date().toISOString(),
      email,
      payload.newsletterOptIn === "yes" ? "Yes" : "No",
      payload.source || "",
      payload.pageUrl || "",
      payload.pageTitle || "",
      payload.userAgent || ""
    ]);

    if (payload.newsletterOptIn === "yes") {
      const newsletterSheet = getSheet_(NEWSLETTER_SHEET_NAME, [
        "Submitted At",
        "Email",
        "Source",
        "Page URL"
      ]);
      newsletterSheet.appendRow([
        payload.submittedAt || new Date().toISOString(),
        email,
        payload.source || "",
        payload.pageUrl || ""
      ]);
    }

    return jsonResponse_({ ok: true });
  } catch (error) {
    return jsonResponse_({ ok: false, error: String(error) });
  } finally {
    lock.releaseLock();
  }
}

function parsePayload_(event) {
  const raw = event && event.postData && event.postData.contents;
  if (raw) {
    try {
      return JSON.parse(raw);
    } catch (error) {
      return {};
    }
  }
  return event && event.parameter ? event.parameter : {};
}

function getSheet_(name, headers) {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = spreadsheet.getSheetByName(name);

  if (!sheet) {
    sheet = spreadsheet.insertSheet(name);
  }

  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
  }

  return sheet;
}

function jsonResponse_(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
