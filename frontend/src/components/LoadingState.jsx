export default function LoadingState({ message = "Loading..." }) {
  return (
    <div className="state-box">
      <div className="spinner" />
      <p>{message}</p>
    </div>
  );
}