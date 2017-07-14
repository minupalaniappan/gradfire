var requirement_group_template = document.getElementById('group_template');
var requirement_course_template = document.getElementById('course_template');
var course_options_template = document.getElementById('course_options_template');
var requirements_root = document.getElementById('requirements');
var AND_REL = 0;
var OR_REL = 1;
var EMPTY_REQ_NODE = {
    name: '',
    rel: 'AND',
    children: [],
    min_units: '',
    max_units: '',
    min_courses: '',
    override_units: false
  };

function nodeFromTemplate(template, pushRequirements) {
  var node = template.cloneNode(true);
  node.style.display = 'block';
  var remove_self_ele = node.getElementsByClassName('remove_self')[0];
  remove_self_ele.addEventListener('click', function(e) {
    node.remove();
    pushRequirements();
  });
  return node;
}

function groupRelToggle(group_ele, ele, ele_is_and, ele_is_or, complement) {
  var unit_inputs = group_ele.getElementsByClassName('units')[0].getElementsByTagName('input');
  var override_units = group_ele.getElementsByClassName('override_units')[0];
  if(ele.className.indexOf('rel_on') != -1) {
    ele.className = 'rel rel_on';
    complement.className = 'rel rel_off';
  }
  else if (complement.className.indexOf('rel_on') != -1) {
    ele.className = 'rel rel_on';
    complement.className = 'rel rel_off';
    if(ele_is_or) {
      override_units.style.display = 'inline';
      for(var i = 0; i < unit_inputs.length; i++) {
        unit_inputs[i].readOnly = false;
      }
    }
    else {
      override_units.style.display = 'none';
      override_units.getElementsByTagName('input')[0].checked = false;
      for(var i = 0; i < unit_inputs.length; i++) {
        unit_inputs[i].readOnly = true;
      }
    }
  }
}

function setupGroupRelToggleListeners(group_ele) {
  var relationships = group_ele.getElementsByClassName('rel');

  function addToggleListener(ele, ele_is_and, ele_is_or, complement) {
    ele.addEventListener('click', function(e) {
      groupRelToggle(group_ele, ele, ele_is_and, ele_is_or, complement);
    });
  }
  addToggleListener(relationships[AND_REL], true, false, relationships[OR_REL]);
  addToggleListener(relationships[OR_REL], false, true, relationships[AND_REL]);
}

function initializeGroupNode(pushRequirements) {
  var group_ele = nodeFromTemplate(requirement_group_template, pushRequirements);
  var group_children = group_ele.getElementsByClassName('children_contents')[0];

  var add_group_ele = group_ele.getElementsByClassName('add_group')[0];
  add_group_ele.addEventListener('click', function(e) {
    var group_ele = appendRequirementGroupToElement(group_children);
    pushRequirements();
    var input_elements = group_ele.getElementsByTagName('input');
    for(var i = 0 ; i < input_elements.length; i++) {
      input_elements[i].addEventListener('keydown', pushOnEnter.bind(this, pushRequirements), false);
    }
  });

  var add_course_options_ele = group_ele.getElementsByClassName('add_course_options')[0];
  add_course_options_ele.addEventListener('click', function(e) {
    var course_options = nodeFromTemplate(course_options_template, pushRequirements);
    group_children.appendChild(course_options);
    var input_elements = course_options.getElementsByTagName('input');
    for(var i = 0 ; i < input_elements.length; i++) {
      input_elements[i].addEventListener('keydown', pushOnEnter.bind(this, pushRequirements), false);
    }
  });

  setupGroupRelToggleListeners(group_ele);
  return group_ele;
}

function appendRequirementGroupToElement(ele) {
  var group_ele = initializeGroupNode();
  ele.appendChild(group_ele);
  return group_ele;
}

function requirementsObjectFromNode(req_node) {
  if(req_node.className.indexOf('course_options') != -1) {
    var course_options = req_node.getElementsByClassName('course_options_input')[0];
    return {
      course_options: course_options.value
    };
  }
  else if(req_node.className.indexOf('course') != -1) {
    var subject_select = req_node.getElementsByClassName('subject_selection')[0];
    var number_input = req_node.getElementsByClassName('number_input')[0];
    return {
      subject: subject_select.value,
      number: number_input.value
    };
  }
  else {
    var name = req_node.getElementsByClassName('group_name')[0].value;
    var rel = req_node.getElementsByClassName('rel_on')[0].textContent;
    var min_courses = req_node.getElementsByClassName('min_courses')[0].value;
    var min_units = req_node.getElementsByClassName('min_units')[0].value;
    var max_units = req_node.getElementsByClassName('max_units')[0].value;
    var override_units = (req_node.getElementsByClassName('override_units')[0]
      .getElementsByTagName('input')[0]
      .checked);


    var children_container = req_node.getElementsByClassName('children_contents')[0];
    var children = [];
    for(var i = 0; i < children_container.childNodes.length; i++) {
      var child = children_container.childNodes[i];
      if(child.nodeType == Node.ELEMENT_NODE) {
        children.push(requirementsObjectFromNode(child));
      }
    }

    return {
      name: name,
      rel: rel,
      min_courses: min_courses,
      min_units: min_units,
      max_units: max_units,
      override_units: override_units,
      children: children
    };
  }
}

function addRequirementNodeFromObject(parent_node, req_obj, pushRequirements) {
  if('children' in req_obj) {
    // req_obj is a group
    var group_node = initializeGroupNode(pushRequirements);
    group_node.getElementsByClassName('group_name')[0].value = req_obj.name;
    if(req_obj.rel == 'OR') {
      var group_rels = group_node.getElementsByClassName('rel');
      groupRelToggle(group_node, group_rels[OR_REL], false, true, group_rels[AND_REL]);
    }

    group_node.getElementsByClassName('min_courses')[0].value = req_obj.min_courses;
    group_node.getElementsByClassName('min_units')[0].value = req_obj.min_units;
    group_node.getElementsByClassName('max_units')[0].value = req_obj.max_units;
    group_node.getElementsByClassName('override_units')[0]
      .getElementsByTagName('input')[0]
      .checked = req_obj.override_units;
    var group_children = group_node.getElementsByClassName('children_contents')[0];
    for(var i = 0; i < req_obj.children.length; i++) {
      var child = req_obj.children[i];
      addRequirementNodeFromObject(group_children, child, pushRequirements);
    }
    parent_node.appendChild(group_node);
    return group_node;
  }
  else {
    // req_obj is a course

    var course_node = nodeFromTemplate(requirement_course_template, pushRequirements);
    var subject_select = course_node.getElementsByClassName('subject_selection')[0];
    subject_select.value = req_obj.subject;

    var number_input = course_node.getElementsByClassName('number_input')[0];
    number_input.value = req_obj.number;
    parent_node.appendChild(course_node);
    return course_node;
  }

}

function pushPrerequisites(reqContainer) {
  var requirements = JSON.parse(JSON.stringify(EMPTY_REQ_NODE));
  var rootChildrenEle = Array.prototype.slice.call(reqContainer.childNodes);
  rootChildrenEle.forEach(function(node) {
    if(node.nodeType == 1 && node.className.indexOf('group') != -1) {
      requirements.children.push(requirementsObjectFromNode(node));
    }
  });

  var req_json = JSON.stringify(requirements);
  var formData = new FormData();
  formData.append('subject', reqContainer.dataset.subject);
  formData.append('number', reqContainer.dataset.number);
  formData.append('term_year', reqContainer.dataset.termYear);
  formData.append('term_month', reqContainer.dataset.termMonth);
  formData.append('req_json', req_json);

  DCS.common.postFormData('/admin/api/store_prerequisites', formData, function(resp) {
    update_requirements_from_node(JSON.parse(resp), reqContainer, pushPrerequisites.bind(this, reqContainer));
    window.location.replace(window.location.href.split('#')[0] + '#' + reqContainer.id);
  });
}

function pushMajorRequirements() {
  var requirements = JSON.parse(JSON.stringify(EMPTY_REQ_NODE));
  var req_groups = requirements_root.childNodes;

  for(var i = 0; i < req_groups.length; i++) {
    var group_node = req_groups[i];
    if(group_node.nodeType == 1 && group_node.className.indexOf('group') != -1) {
      requirements.children.push(requirementsObjectFromNode(group_node));
    }
  }

  var req_json_field = document.getElementById('major_req_json');
  req_json_field.value = JSON.stringify(requirements);

  var formData = new FormData(update_major_form);
  var xhr = new XMLHttpRequest();
  var major_update_btn = document.getElementById('update_major');
  major_update_btn.disabled = true;

  xhr.onreadystatechange = function() {
    if (xhr.readyState == XMLHttpRequest.DONE) {
      major_update_btn.disabled = false;
      if(xhr.status == 200) {
        pull_requirements();
      }
    }
  };
  xhr.open('POST', 'api/store_major_reqs');
  xhr.send(formData);
}

function update_requirements_from_node(req_node, requirements_root, pushRequirements) {
  // Reset req view
  var old_req_nodes = [];
  for(var i = 0; i < requirements_root.childNodes.length; i++) {
    var child = requirements_root.childNodes[i];
    child.remove();
  }
  var group_node = addRequirementNodeFromObject(requirements_root, req_node, pushRequirements);
  var input_elements = group_node.getElementsByTagName('input');
  for(var i = 0 ; i < input_elements.length; i++) {
    input_elements[i].addEventListener('keydown', pushOnEnter.bind(this, pushRequirements), false);
  }
}

function pull_requirements() {
  var xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function() {
    if (xhr.readyState == XMLHttpRequest.DONE) {
      var major_update_btn = document.getElementById('update_major');
      if(xhr.status == 200) {
        var reqTree = (xhr.responseText != '') ? JSON.parse(xhr.responseText) : '';
        update_requirements_from_node(reqTree, requirements_root, pushMajorRequirements);
        var total_units_lo = document.getElementById('major_units_low');
        var total_units_hi = document.getElementById('major_units_hi');
        total_units_lo.innerText = req_node.min_units;
        total_units_hi.innerText = req_node.max_units;
        major_update_btn.disabled = false;
      } else {
        major_update_btn.disabled = true;
      }
    }
  };
  xhr.open('GET', 'api/major_reqs_by_id?major_id=' + major_dropdown.value);
  xhr.send(null);
}

var update_major_form = document.getElementById('update_major_form');
if(update_major_form) {
  update_major_form.addEventListener('submit', function(e) {
    e.preventDefault();
    pushMajorRequirements()
  });
  var major_dropdown = document.getElementById('select_major');
  major_dropdown.addEventListener('change', pull_requirements);
}
function pushOnEnter(func, keypress) {
  if(keypress.keyCode == 13) {
    keypress.preventDefault();
    keypress.stopPropagation();
    func();
  }
}
