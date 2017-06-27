import React from 'react'
import { gql, graphql } from 'react-apollo'

const query = gql`
{
  currentUser {
    id
  }
}
`

class CreateView extends React.Component {
  componentWillUpdate(nextProps) {
    if (!nextProps.data.loading && nextProps.data.currentUser === null) {
      window.location.replace('/login/')
    }
  }

  render() {
    let { data } = this.props
    if (data.loading || data.currentUser === null) {
      return <div>Loading...</div>
    }
    return <div>CreateView</div>
  }
}

CreateView = graphql(query)(CreateView)
export default CreateView
