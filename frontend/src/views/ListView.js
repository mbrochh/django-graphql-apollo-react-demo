import React from 'react'
import { Link } from 'react-router-dom'
import { gql, graphql } from 'react-apollo'

const query = gql`
{
  allMessages {
    id, message
  }
}
`

class ListView extends React.Component {
  render() {
    let { data } = this.props
    if (data.loading || !data.allMessages) {
      return <div>Loading...</div>
    }
    return (
      <div>
        {data.allMessages.map(item => (
          <p key={item.id}>
            <Link to={`/messages/${item.id}/`}>
              {item.message}
            </Link>
          </p>
        ))}
      </div>
    )
  }
}

ListView = graphql(query)(ListView)
export default ListView
