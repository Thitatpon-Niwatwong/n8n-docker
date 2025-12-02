import json
import os

file_path = r'C:\Users\thita\docker\workflows\RDVATLookup.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 1. Update HTTP Request Node to continue on fail
http_node_found = False
for node in data['nodes']:
    if node['name'] == 'HTTP: RD VAT Lookup':
        node['onError'] = 'continueRegularOutput'
        http_node_found = True
        print("Updated 'HTTP: RD VAT Lookup' to continue on error.")
        break

if not http_node_found:
    print("Error: 'HTTP: RD VAT Lookup' node not found.")

# 2. Update Normalize RD Response Code
# The new code handles n8n error structures explicitly
new_js_code = r"""
const items = $input.all();
const out = [];

function clean(val) {
  const x = String(val ?? '').trim();
  return x === '-' ? '' : x;
}

function getField(obj, field) {
  const sr = obj?.["soap:Envelope"]?.["soap:Body"]?.ServiceResponse?.ServiceResult ?? {};
  const v = sr[field];
  if (v == null) return '';
  if (typeof v === 'string' || typeof v === 'number') return String(v);
  if (v.anyType !== undefined) {
    const a = v.anyType;
    if (typeof a === 'string' || typeof a === 'number') return String(a);
    if (a && typeof a._ !== 'undefined') return String(a._);
  }
  if (typeof v._ !== 'undefined') return String(v._);
  return '';
}

function parseError(obj) {
  // 1. Check for SOAP Error (Business Logic Error from RD)
  const sr = obj?.["soap:Envelope"]?.["soap:Body"]?.ServiceResponse?.ServiceResult ?? {};
  if (sr.vmsgerr) return clean(sr.vmsgerr);

  // 2. Check for n8n Node Error (Network/Timeout/HTTP 5xx)
  if (obj.error) {
     return clean(obj.error.message || obj.error.description || JSON.stringify(obj.error));
  }
  
  // 3. Check for raw errorMessage field
  if (obj.errorMessage) return clean(obj.errorMessage);

  return '';
}

for (let i=0; i<items.length; i++) {
  const item = items[i];
  const json = item.json;
  
  // Check for error first
  const errMsg = parseError(json);
  
  // If error exists, return failed status immediately
  if (errMsg) {
      out.push({
        json: {
          ...json,
          rd_vat_id: json.vat_id || '', // Keep original input if possible
          rd_branch_number: json.branch_id || '',
          rd_company_name: '',
          rd_address_raw: '',
          rd_error_message: errMsg,
          rd_success: false
        },
        pairedItem: { item: i }
      });
      continue;
  }

  // Normal parsing
  const vatId = clean(getField(json, 'vNID'));
  const branchRaw = clean(getField(json, 'vBranchNumber'));
  const branchNumber = branchRaw === '0' || branchRaw === '' ? '00000' : branchRaw.padStart(5, '0');
  
  const titleName = clean(getField(json, 'vtitleName'));
  const companyNameMain = clean(getField(json, 'vName'));
  const companyName = `${titleName} ${companyNameMain}`.trim();

  const addressObj = {
    houseNo: clean(getField(json, 'vHouseNumber')),
    moo: clean(getField(json, 'vMooNumber')),
    village: clean(getField(json, 'vVillageName')),
    building: clean(getField(json, 'vBuildingName')),
    floor: clean(getField(json, 'vFloorNumber')),
    room: clean(getField(json, 'vRoomNumber')),
    soi: clean(getField(json, 'vSoiName')),
    street: clean(getField(json, 'vStreetName')),
    subDistrict: clean(getField(json, 'vThambol')),
    district: clean(getField(json, 'vAmphur')),
    province: clean(getField(json, 'vProvince')),
    postcode: clean(getField(json, 'vPostCode')),
    yaek: clean(getField(json, 'vYaek')),
  };

  // Build raw address string
  const parts = [];
  if (addressObj.houseNo) parts.push(addressObj.houseNo);
  if (addressObj.moo) parts.push("หมู่ " + addressObj.moo);
  if (addressObj.village) parts.push("หมู่บ้าน" + addressObj.village);
  if (addressObj.building) parts.push("อาคาร" + addressObj.building);
  if (addressObj.floor) parts.push("ชั้น " + addressObj.floor);
  if (addressObj.room) parts.push("ห้อง " + addressObj.room);
  if (addressObj.soi) parts.push("ซอย" + addressObj.soi);
  if (addressObj.yaek) parts.push("แยก " + addressObj.yaek);
  if (addressObj.street) parts.push("ถนน" + addressObj.street);
  
  const isBangkok = /กรุงเทพมหานคร/.test(addressObj.province);
  if (addressObj.subDistrict) parts.push((isBangkok ? "แขวง " : "ต.") + addressObj.subDistrict);
  if (addressObj.district) parts.push((isBangkok ? "เขต " : "อ.") + addressObj.district);
  
  if (addressObj.province) {
    parts.push(isBangkok ? addressObj.province : "จ." + addressObj.province);
  }
  if (addressObj.postcode) parts.push(addressObj.postcode);
  
  const address_raw = parts.join(" ").replace(/\s+/g, " ").trim();

  out.push({
    json: {
      ...json, // keep original input
      rd_vat_id: vatId,
      rd_branch_number: branchNumber,
      rd_company_name: companyName,
      rd_address_raw: address_raw,
      rd_error_message: '',
      rd_success: Boolean(vatId)
    },
    pairedItem: { item: i }
  });
}

return out;
"""

code_node_found = False
for node in data['nodes']:
    if node['name'] == 'Normalize RD Response':
        node['parameters']['jsCode'] = new_js_code
        code_node_found = True
        print("Updated 'Normalize RD Response' code.")
        break

if not code_node_found:
    print("Error: 'Normalize RD Response' node not found.")

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Done.")
