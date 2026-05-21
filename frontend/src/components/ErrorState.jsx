export default function ErrorState({ message = "Something went wrong." }) {
  return (
    <div className="error-box">
      <strong>Error</strong>
      <p>{message}</p>
    </div>
  );
}