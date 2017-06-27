import React from 'react'
import { Link } from 'react-router-dom'
import { gql, graphql } from 'react-apollo'
import queryString from 'query-string'

const query = gql`
query ListViewSearch($search: String, $endCursor: String) {
  allMessages(first: 2, message_Icontains: $search, after: $endCursor) {
    edges {
      node {
        id, message
      }
    },
    pageInfo {
      hasNextPage,
      hasPreviousPage,
      startCursor,
      endCursor
    }
  }
}
`

class ListView extends React.Component {
  handleSearchSubmit(e) {
    e.preventDefault()
    let data = new FormData(this.form)
    let query = `?search=${data.get('search')}`
    this.props.history.push(`/${query}`)
  }

  loadMore() {
    let { data, location } = this.props
    data.fetchMore({
      query: query,
      variables: {
        search: queryString.parse(location.search).search,
        endCursor: data.allMessages.pageInfo.endCursor,
      },
      updateQuery: (prev, next) => {
        const newEdges = next.fetchMoreResult.allMessages.edges
        const pageInfo = next.fetchMoreResult.allMessages.pageInfo
        return {
          allMessages: {
            edges: [...prev.allMessages.edges, ...newEdges],
            pageInfo,
          },
        }
      },
    })
  }

  render() {
    let { data } = this.props
    if (data.loading || !data.allMessages) {
      return <div>Loading...</div>
    }
    return (
      <div>
        <form
          ref={ref => (this.form = ref)}
          onSubmit={e => this.handleSearchSubmit(e)}
        >
          <input type="text" name="search" />
          <button type="submit">Search</button>
        </form>
        {data.allMessages.edges.map(item => (
          <p key={item.node.id}>
            <Link to={`/messages/${item.node.id}/`}>
              {item.node.message}
            </Link>
          </p>
        ))}
        {data.allMessages.pageInfo.hasNextPage &&
          <button onClick={() => this.loadMore()}>Load more...</button>}
      </div>
    )
  }
}

const queryOptions = {
  options: props => ({
    variables: {
      search: queryString.parse(props.location.search).search,
    },
  }),
}

ListView = graphql(query, queryOptions)(ListView)
export default ListView
