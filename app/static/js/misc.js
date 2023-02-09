/*!
Script provides misc functionality on webpage
*/

window.addEventListener('DOMContentLoaded', event => {
const submit_btn_element = document.getElementById("add_new_note_toggle");
submit_btn_element.addEventListener("click", clearInputFormValues);
// var myCollapsible = document.getElementById('collapseView')
// myCollapsible.addEventListener('show.bs.collapse', clearInputValues)
});

function clearInputFormValues() {
  document.getElementById("note_forms_title_inputarea").value = "";
  document.getElementById("note_forms_text_inputarea").value = "";
}

function editNoteFunction(title,text) {
  //Function to Provide Edit Functionality, At the moment gets it from values stored in HTML
  // TODO: Notes Should come from App Directly
  var myCollapsible = document.getElementById('collapseView')
  myCollapsible.className = "collapse show"
  document.getElementById("note_forms_title_inputarea").value = title;
  document.getElementById("note_forms_text_inputarea").value = text;
  window.scrollTo(0, 0);
}

function deleteNoteFunction(url,note_id,user_id) {
location.href = url + "?id=" + note_id + "&user_id=" + user_id;
}

function myscrollTop() {
  window.scrollTo(0, 0);
};