import React from 'react'

export default class LogoutView extends React.Component {
  handleClick() {
    localStorage.removeItem('token')
    window.location.replace('/')
  }

  render() {
    return (
      <div>
        <h1>Logout</h1>
        <button onClick={() => this.handleClick()}>Logout</button>
      </div>
    )
  }
}
