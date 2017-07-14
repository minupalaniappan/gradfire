var updateMajorSelect = document.getElementById('select_major_to_update');
var updateNameField = updateMajorSelect.parentElement.getElementsByClassName('major_name')[0];
var updateVariantField = updateMajorSelect.parentElement.getElementsByClassName('major_variant')[0];
updateMajorSelect.addEventListener('change', function(e) {
  var selectedOption = e.target.selectedOptions[0];
  updateNameField.value = selectedOption.dataset.name;
  updateVariantField.value =  selectedOption.dataset.variant;
});
