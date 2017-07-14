import * as common from 'common'


export var InfiniteList = React.createClass({
    getDefaultProps: function () {
        return ({
            redirectURL: null,
            noContentText: ''
        })
    },
    getInitialState: function() {
        return {
            elements: [],
            isInfiniteLoading: true,
            page: 0,
            isAtEnd: false,
        }
    },

    buildElements: function(page) {
        this.setState({
            isInfiniteLoading: true,
            page: page
        }, function(that = this) {
            that.props.fetchComponentsWithCallback(page, function(elements) {
                var endState = {isInfiniteLoading: false}
                if(elements.length == 0) {
                    endState['isAtEnd'] = true;
                } else {
                    endState['elements'] = that.state.elements.concat(elements)
                }
                that.setState(endState);
            });
        });
    },

    handleInfiniteLoad: function() {
        var that = this;
        if (!this.state.isAtEnd) {
            this.buildElements(this.state.page + 1);
        } else {
            this.setState({
                isInfiniteLoading: false,
                isAtEnd: true
            });
        }

    },
    componentDidMount: function() {
        this.handleInfiniteLoad();
    },
    elementInfiniteLoad: function() {
        return (<div className="column-12 center padding-1"><button className="infinite-list-item load center column-2 wrapper-2">
            <p>Loading...</p>
        </button></div>);
    },
    render: function() {
        var contentNone, loading;
        if(this.state.elements.length == 0 && this.state.isAtEnd) {
            contentNone = (<p className={"center column-12 regular"}>
                {this.props.noContentText}
                </p>);
        }

        if (this.state.isInfiniteLoading)
            loading = this.elementInfiniteLoad();
        else
            loading = null;

        return (<div>
                    {this.state.elements}
                    {contentNone}
                </div>);
    }
});