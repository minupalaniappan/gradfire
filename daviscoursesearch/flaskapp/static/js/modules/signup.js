export var signup = {
    roleListener: function() {

    },
    removeMajor: function(e) {
      e.target.parentNode.remove();
    },
    addMajor: function(e) {
      var new_major_select_container = this.major_select_container.cloneNode(true);
      var major_select = new_major_select_container.getElementsByClassName('major_select')[0];
      major_select.name = 'major_' + (Math.floor(Math.random() * 100000)).toString();

      var major_options = major_select.getElementsByTagName('option');
      for(var i = 0; i < major_options.length; i++) {
        major_options[i].selected = false;
      }

      var remove_major_btn = new_major_select_container.getElementsByClassName('remove_major')[0];
      remove_major_btn.style.display = '';
      remove_major_btn.addEventListener('click', this.removeMajor.bind(this));

      this.major_input_container.appendChild(new_major_select_container);
    },
    _init: function() {
      this.roleListener();
      this.major_input_container = document.getElementById('major_input_container');
      this.major_select_container = document.getElementsByClassName('major_select_and_remove')[0];

      var add_major_btn = document.getElementById('add_major');
      add_major_btn.addEventListener('click', this.addMajor.bind(this));
    }
}