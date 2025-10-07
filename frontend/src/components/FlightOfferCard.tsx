import { FaPlane } from 'react-icons/fa';

export default function FlightOfferCard({ flight }) {
  const { itineraries, price } = flight;
  const there = itineraries[0].segments;
  const back = itineraries.length > 1 ? itineraries[1].segments : null;

  const formatTime = (datetime) => new Date(datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const formatDate = (datetime) => new Date(datetime).toLocaleDateString([], { month: 'short', day: 'numeric' });

  const renderSegment = (segment, isLast) => (
    <div key={segment.id} className={`flex items-center gap-2 ${!isLast ? 'mb-2' : ''}`}>
      <FaPlane className="text-blue-500" />
      <div className="text-sm">
        <span className="font-semibold">{segment.departure.iataCode}</span> {formatTime(segment.departure.at)} - <span className="font-semibold">{segment.arrival.iataCode}</span> {formatTime(segment.arrival.at)}
      </div>
      <div className="text-xs text-gray-500">{segment.carrierCode} {segment.number}</div>
    </div>
  );

  return (
    <div className="bg-white shadow-lg rounded-lg overflow-hidden mb-6 transition-transform hover:scale-105">
      <div className="p-4 border-b">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-bold text-lg text-blue-800">{there[0].departure.iataCode} to {there[there.length - 1].arrival.iataCode}</h3>
            <p className="text-sm text-gray-600">{formatDate(there[0].departure.at)}</p>
          </div>
          <div className="text-right">
            <div className="font-extrabold text-2xl text-blue-600">${price.total}</div>
            <div className="text-xs text-gray-500">Total price for all passengers</div>
          </div>
        </div>
      </div>
      <div className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-semibold text-md mb-2 border-b pb-1">Departure</h4>
            {there.map((segment, index) => renderSegment(segment, index === there.length - 1))}
          </div>
          {back && (
            <div>
              <h4 className="font-semibold text-md mb-2 border-b pb-1">Return</h4>
              {back.map((segment, index) => renderSegment(segment, index === back.length - 1))}
            </div>
          )}
        </div>
      </div>
      <div className="bg-blue-50 p-4 text-right">
        <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition-colors">
          Select Flight
        </button>
      </div>
    </div>
  );
}
