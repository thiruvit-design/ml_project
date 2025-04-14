import React, { useState } from "react";
import "../styles/homepage.css"; // Import CSS
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

function HomePage() {
    const [latitude, setLatitude] = useState("");
    const [longitude, setLongitude] = useState("");
    const [date, setDate] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handlePredict = async () => {
        if (!latitude || !longitude || !date) {
            setError("Please enter all fields");
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/api/weather?lat=${latitude}&lon=${longitude}&date=${date}`
            );
            const data = await response.json();

            if (response.ok) {
                setResult(data);
            } else {
                setError(data.error || "Failed to fetch data");
            }
        } catch (error) {
            setError("Error fetching data");
        } finally {
            setLoading(false);
        }
    };

    const chartData = result?.solar_radiation
        ? Object.entries(result.solar_radiation).map(([time, value]) => ({
            time,
            radiation: Number(parseFloat(value).toFixed(2)), 
    })): [];

    return (
        <div className="homepage">
            <p style={{ margin: "0px" }}>Solar Cooker Performance Prediction</p>
            <div className="box">
                <div className="input-container">
                    <p style={{ margin: "0 0 0 10px" }}>Enter the latitude, longitude and date</p>
                    <input type="text" placeholder="Latitude" value={latitude} onChange={(e) => setLatitude(e.target.value)}/>
                    <input type="text" placeholder="Longitude" value={longitude} onChange={(e) => setLongitude(e.target.value)}/>
                    <input type="text" placeholder="Date (YYYYMMDD)" value={date} onChange={(e) => setDate(e.target.value)}/>
                    <button onClick={handlePredict} disabled={loading}>
                        {loading ? <span className="loader"></span> : "Predict Performance"}
                    </button>
                </div>

                <div className="radiation">
                    {result ? (
                    <>
                        <p className="head">Location: {result.location || "Unknown"}</p>
                        <p className="head">Solar Radiation Data:</p>
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="gray" strokeOpacity={0.1} />
                            <XAxis dataKey="time" stroke="gray" strokeOpacity={0.3} />
                            <YAxis domain={[0, "auto"]} stroke="gray" strokeOpacity={0.3} />
                            <Tooltip contentStyle={{ backgroundColor: "rgb(34, 34, 34)", color: "white", borderRadius: "10px", border: "none" }} 
                            itemStyle={{ color: "white" }}
                            formatter={(value) => [`${value} W/m²`, "Solar Radiation"]}
                            labelFormatter={(label) => `Time: ${label}`}
                            />
                                <Line type="monotone" dataKey="radiation" stroke="rgb(237, 42, 11)" strokeWidth={3} strokeOpacity={0.5}  />
                            </LineChart>
                        </ResponsiveContainer>
                    </>
                    ) : (
                        <p></p>
                    )}
                </div>
            </div>


            <div className="result">
                <p style={{margin:"0px", fontSize:"20px"}}>Model Prediction:</p>

            </div>
        </div>
    );
}

export default HomePage;
