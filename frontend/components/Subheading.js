export default function Subheading(props) {
    return (
        <div {...props}>
            <div className='text-3xl font-bold'>
                <h2>{props.children}</h2>
            </div>
        </div>
    )
}
