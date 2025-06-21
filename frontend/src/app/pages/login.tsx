import "../../assets/css/pages/login.css";
import logo from "../../assets/images/CC_logo.png";

function Login() {
    return (
        <div className="content">
            <section id="login">
                <form>
                    <div className="imgcontainer">
                        <img
                            src={logo}
                            style={{
                                maxWidth: "20vw",
                                maxHeight: "20vh",
                                borderRadius: "100%",
                            }}
                            alt="Avatar"
                            className="avatar"
                        />
                    </div>

                    <div className="container">
                        <label htmlFor="uname">
                            <b>Username</b>
                        </label>
                        <input
                            type="text"
                            placeholder="Enter Username"
                            name="uname"
                            required
                        />

                        <label htmlFor="psw">
                            <b>Password</b>
                        </label>
                        <input
                            type="password"
                            placeholder="Enter Password"
                            name="psw"
                            required
                        />

                        <button className="button" type="submit">
                            Login
                        </button>
                        <label>
                            <input type="checkbox" name="remember" /> Remember
                            me
                        </label>
                    </div>
                </form>
            </section>
        </div>
    );
}

export default Login;
