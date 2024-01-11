function ChooseImage(name: string) {
    const theme = document.documentElement.getAttribute("data-theme");
    return `/images/${theme}/${name}`
}

export default ChooseImage