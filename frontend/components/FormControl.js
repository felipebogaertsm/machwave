export default function FormControl({ title, type = 'text', value = '' }) {
    return (
        <div
            className="
                flex flex-col space-y-2
            "
        >
            <label>{title}</label>
            <input type={type}></input>
        </div>
    )
}
