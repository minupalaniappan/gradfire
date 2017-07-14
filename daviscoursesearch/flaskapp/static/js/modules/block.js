import * as common from 'common'
import * as update from 'update'
import * as infiniteload from 'infiniteload'
import * as cards from 'cards'

export var GenericBlock = React.createClass({
	propTypes: {
		noContentText: React.PropTypes.string,
	},
	getDefaultProps: function () {
		return ({
			column_size: 12,
			object_count: null,
			id: null,
			data: [],
			hasData: false,
			hasFunctions: false,
			type: null,
			fetchComponentsWithCallback: null,
			prependComponents: []
		});
	},
	render: function () {
		var component = (<infiniteload.InfiniteList ref="infiniteList"
			key={common.createReactRootIndex()}
			fetchComponentsWithCallback={this.props.fetchComponentsWithCallback}
			type={this.props.type}
			noContentText={this.props.noContentText}
		/>);

		return (
			<div>
				<div id = {this.props.id} className={"column-12"}>
					<div>
						{ this.props.prependComponents }
						{ component }
					</div>
				</div>
			</div>
		);
	}
});
