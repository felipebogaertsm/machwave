function Card(props) {
    return (
        <div {...props}>
            <div className="relative bg-zinc-100 shadow-xl rounded-2xl p-4">
                {props.children}
            </div>
        </div>
    )
}

export default Card
