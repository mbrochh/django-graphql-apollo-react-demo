import React from 'react'
import { gql, graphql } from 'react-apollo'

const mutation = gql`
mutation CreateView($message: String!) {
  createMessage(message: $message) {
    status,
    formErrors,
    message {
      id
    }
  }
}
`

const query = gql`
{
  currentUser {
    id
  }
}
`

class CreateView extends React.Component {
  constructor(props) {
    super(props)
    this.state = { formErrors: null }
  }

  componentWillUpdate(nextProps) {
    if (!nextProps.data.loading && nextProps.data.currentUser === null) {
      window.location.replace('/login/')
    }
  }

  handleSubmit(e) {
    e.preventDefault()
    let data = new FormData(this.form)
    this.props
      .mutate({ variables: { message: data.get('message') } })
      .then(res => {
        if (res.data.createMessage.status === 200) {
          window.location.replace('/')
        }
        if (res.data.createMessage.status === 400) {
          this.setState({
            formErrors: JSON.parse(res.data.createMessage.formErrors),
          })
        }
      })
      .catch(err => {
        console.log('Network error')
      })
  }

  render() {
    let { data } = this.props
    if (data.loading || data.currentUser === null) {
      return <div>Loading...</div>
    }
    return (
      <div>
        <h1>Create Message</h1>
        <form
          ref={ref => (this.form = ref)}
          onSubmit={e => this.handleSubmit(e)}
        >
          <div>
            <label>Message:</label>
            <textarea name="message" />
            {this.state.formErrors &&
              this.state.formErrors.message &&
              <p>Error: {this.state.formErrors.message}</p>}
          </div>
          <button type="submit">Submit Message</button>
        </form>
      </div>
    )
  }
}

CreateView = graphql(query)(CreateView)
CreateView = graphql(mutation)(CreateView)
export default CreateView
