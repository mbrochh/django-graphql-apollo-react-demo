import React from 'react'

export default class LoginView extends React.Component {
  handleSubmit(e) {
    e.preventDefault()
    let data = new FormData(this.form)
    fetch('http://localhost:8000/api-token-auth/', {
      method: 'POST',
      body: data,
    })
      .then(res => {
        res.json().then(res => {
          if (res.token) {
            localStorage.setItem('token', res.token)
            window.location.replace('/')
          }
        })
      })
      .catch(err => {
        console.log('Network error')
      })
  }

  render() {
    return (
      <div>
        <h1>LoginView</h1>
        <form
          ref={ref => (this.form = ref)}
          onSubmit={e => this.handleSubmit(e)}
        >
          <div>
            <label>Username:</label>
            <input type="text" name="username" />
          </div>
          <div>
            <label>Password:</label>
            <input type="password" name="password" />
          </div>
          <button type="submit">Login</button>
        </form>
      </div>
    )
  }
}
