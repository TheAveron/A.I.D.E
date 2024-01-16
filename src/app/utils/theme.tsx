import "../../assets/styles/theme.css";


function changetheme() {
    const data_theme = document.documentElement.getAttribute("data-theme");
    const button = document.getElementById("theme-img");

    if (data_theme == "light") {
        document.documentElement.setAttribute("data-theme", "dark");
        button?.setAttribute("src", `/A.I.D.E/images/dark/moon.png`);
    } else {
        document.documentElement.setAttribute("data-theme", "light");
        button?.setAttribute("src", `/A.I.D.E/images/light/sun.png`);
    }
}

function ChooseThemeIcon() {
    const data_theme = document.documentElement.getAttribute("data-theme");
    if (data_theme == "light") {
        return `/A.I.D.E/images/${data_theme}/sun.png`;
    } else {
        return `/A.I.D.E/images/${data_theme}/moon.png`;
    }
}

function ThemeChoice() {
    return (
        <>
            <button onClick={changetheme} id="theme-button">
                <img id="theme-img" src={ChooseThemeIcon()} />
            </button>
        </>
    );
}

export default ThemeChoice;
