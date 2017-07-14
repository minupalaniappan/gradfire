import * as common from 'common'
import {Courses} from 'api'

import {Draft} from '../lib/Draft'

export const colorStyleMap = {
    headerOne: {
      fontWeight: '700',
      fontSize: '30px',
      color: '#333',
    },
    headerTwo: {
      fontWeight: '700',
      fontSize: '23px',
      color: '#787878',
    },
    headerThree: {
      fontWeight: '400',
      fontSize: '19px',
      color: '#B5B5B5',
    },
    headerFour: {
      fontWeight: '400',
      fontSize: '15px',
      color: '#2E2E2E',
    },
    block: {
      color: 'rgba(0, 0, 255, 1.0)',
    },
    unorderedList: {
    	listStyleType: 'circle',
    },
    orderedList: {
    	listStyleType: 'decimal',
    },
};

export const keyCodes = {
	49: 'h1',
	50: 'h2',
	51: 'h3',
	52: 'h4',
	53: 'h5',
	54: 'h6',
	85: 'ol',
	79: 'ul',
	83: 'save'
}


const {Editor,EditorState, RichUtils, inlineTags, getDefaultKeyBinding, KeyBindingUtil} = Draft
const {hasCommandModifier} = KeyBindingUtil;

export var profNote = React.createClass({
    propTypes: function() {
        note: React.PropTypes.object.isRequired
    },
	getDefaultProps: function () {
		return ({
			inlineTools: [
				{label: 'Bold', value: 'BOLD'},
				{label: 'Code', value: 'CODE'},
				{label: 'Strike', value: 'STRIKETHROUGH'},
				{label: 'Italic', value: 'ITALIC'},
				{label: 'Underline', value: 'UNDERLINE'},
			],
			exclusiveTools: [
				{label: 'H1', value: 'header-one'},
		        {label: 'H2', value: 'header-two'},
		        {label: 'H3', value: 'header-three'},
		        {label: 'H4', value: 'header-four'},
		        {label: 'H5', value: 'header-five'},
		        {label: 'H6', value: 'header-six'},
		        {label: 'Blockquote', value: 'blockquote'},
		        {label: 'UL', value: 'unordered-list-item'},
		        {label: 'OL', value: 'ordered-list-item'},
			]
		})
	},
	getInitialState: function () {
        var editorState;
        if(this.props.note) {
            let contentState = Draft.convertFromRaw(this.props.note)
            editorState = EditorState.createWithContent(contentState)
        }
        else {
            editorState = EditorState.createEmpty()
        }
		return ({
			editorState: editorState,
			readOnly: false
		});
	},
	_onStyleClick(tooltip, isExclusive) {
		if (isExclusive) {
          this.onChange(RichUtils.toggleBlockType(this.state.editorState, tooltip));
		}
		else
	    	this.onChange(RichUtils.toggleInlineStyle(this.state.editorState, tooltip));
	},
	handleKeyCommand(command) {
		const newState = RichUtils.handleKeyCommand(this.state.editorState, command);
		if (newState) {
	      this.onChange(newState);
	      return 'handled';
	    }
    	return 'not-handled';
	},
	_swapReadOnly: function () {
        if(!this.state.readOnly) {
            let contentState = this.state.editorState.getCurrentContent()
            let note_plain = contentState.getPlainText()
            let note_js_raw = Draft.convertToRaw(this.state.editorState.getCurrentContent())
            let note_json = JSON.stringify(note_js_raw)

            Courses.reviseInstructorNote(window.COURSE['subject'], window.COURSE['number'],
                note_json,
                note_plain,
                ()=>{console.log("saved")})
        }

		this.setState({
			readOnly: !this.state.readOnly
		});
	},
	myKeyBindingFn: function (e) {
	  if (hasCommandModifier(e)) {
	  		if (keyCodes[e.keyCode]) {
	  			if (keyCodes[e.keyCode] === 'save') {
	  				var plainText = editorState.getCurrentContent().getPlainText();
	  				e.preventDefault();
	  				this.setState({
	  					readOnly: !this.state.readOnly
	  				})
	  			}
	  			else
	  				return (keyCodes[e.keyCode]);
	  		}
	  		return (getDefaultKeyBinding(e));
	  }
	  return (getDefaultKeyBinding(e));

	},
	onChange: function (editorState) {
		this.setState({editorState});
	},
	focus:function () {
		this.refs.editor.focus();
	},
	render: function () {
		var editorState = this.state.editorState;
		let className = 'RichEditor-editor';
		var currentStyle = editorState.getCurrentInlineStyle();
		var contentState = editorState.getCurrentContent();
		var blockType = editorState
        .getCurrentContent()
        .getBlockForKey(editorState.getSelection().getStartKey())
        .getType()

        if (editorState.getCurrentInlineStyle().size || RichUtils.getCurrentBlockType(editorState) !== 'unstyled') {
        	className += ' RichEditor-hidePlaceholder';
        }

      	var contentState = editorState.getCurrentContent();

      	if (!contentState.hasText()) {
        	if (contentState.getBlockMap().first().getType() !== 'unstyled') {
          		className += ' RichEditor-hidePlaceholder';
        	}
      	}
		return (
			<div className = "column-12 card-col padding-side-2">
				<div className = "tool-set padding-1 border">

					{this.props.inlineTools.map((style) =>
		              <p
		              	key = {style.label}
		              	onClick= {(!this.state.readOnly) ? this._onStyleClick.bind(this, style.value, null) : null}
		                className = {(currentStyle.has(style.value)) ? "small" + " selected" : (this.state.readOnly) ? "small" : "small"}
		                >
		                {style.label}
		                </p>
		            )}
		            {this.props.exclusiveTools.map((style) =>
		              <p
		              	key = {style.label}
		              	onClick= {(!this.state.readOnly) ? this._onStyleClick.bind(this, style.value, true, null) : null}
		                className = {(style.value === blockType) ? "small " + " selected" : (this.state.readOnly) ? "small" : "small"}
		                >
		                {style.label}
		                </p>
		            )}
				</div>
				<div className={className + " form-backdrop margin-1 type"} onClick={this.focus}>
					<Editor editorState={this.state.editorState}
							handleKeyCommand={this.handleKeyCommand}
							keyBindingFn={this.myKeyBindingFn}
							onChange={this.onChange}
							placeholder={'Pinned professor notes for this class'}
							spellCheck = {true}
							customStyleMap={colorStyleMap}
							readOnly={this.state.readOnly}
							ref = {'editor'}
							/>
					<div className="column-12 right padding-2" style = {{textAlign: 'right'}}>
						<button
			              	onClick= {this._swapReadOnly.bind(this, null)}
			                className = {(this.state.readOnly) ? "loadAlternate small column-2 wrapper-2 right":"loadAlternate small column-2 wrapper-2 right"}
			                >
		                {(this.state.readOnly) ? "EDIT":"SAVE"}
		                </button>
	                </div>
				</div>

			</div>
		);
	}
});

export var profNoteToStudent = React.createClass({
	getDefaultProps: function () {
		return ({
			subject: null, 
			number: null
		});
	},
	fetchNote: function () {
		Courses.instructorNote(this.props.subject, this.props.number, (elem) => {
			console.log(elem);
		}); 
	}, 
	render: function () {
		this.fetchNote();
		return (
			<div className = "profNoteToStudent">
			</div>
		)
	}
})