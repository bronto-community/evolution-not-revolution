# The (slightly simplified) Nuremberg U-Bahn network and its timetable.
import time

U1 = [
    "Fürth Hardhöhe", "Klinikum", "Stadthalle", "Rathaus", "Fürth Hauptbahnhof",
    "Jakobinenstraße", "Stadtgrenze", "Muggenhof", "Eberhardshof", "Maximilianstraße",
    "Bärenschanze", "Gostenhof", "Plärrer", "Weißer Turm", "Lorenzkirche", "Hauptbahnhof",
    "Aufseßplatz", "Maffeiplatz", "Frankenstraße", "Hasenbuck", "Bauernfeindstraße",
    "Messe", "Langwasser Nord", "Gemeinschaftshaus", "Langwasser Mitte",
    "Scharfreiterring", "Langwasser Süd",
]
U2 = [
    "Röthenbach", "Hohe Marter", "Schweinau", "St. Leonhard", "Rothenburger Straße",
    "Plärrer", "Opernhaus", "Hauptbahnhof", "Wöhrder Wiese", "Rathenauplatz", "Rennweg",
    "Schoppershof", "Nordostbahnhof", "Herrnhütte", "Ziegelstein", "Flughafen",
]
U3 = [
    "Gustav-Adolf-Straße", "Sündersbühl", "Rothenburger Straße", "Plärrer", "Opernhaus",
    "Hauptbahnhof", "Wöhrder Wiese", "Rathenauplatz", "Maxfeld", "Kaulbachplatz",
    "Friedrich-Ebert-Platz", "Klinikum Nord", "Nordwestring",
]
HEADWAY_MIN = {"U1": 5, "U2": 5, "U3": 10}


def stop_id(name):
    """'Plärrer' -> 'plaerrer'"""
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), (" ", "-"), (".", "")):
        name = name.lower().replace(a, b)
    return name


LINES = {line: [stop_id(s) for s in stops] for line, stops in (("U1", U1), ("U2", U2), ("U3", U3))}
STOPS = {stop_id(s): s for s in U1 + U2 + U3}


def timetable(stop, count=5, next_stops=5):
    """The next departures at a stop from the printed timetable, with the next stops of each trip."""
    now_min = time.time() / 60
    departures = []
    for line, stops in LINES.items():
        for direction in (stops, stops[::-1]):
            if stop not in direction or direction[-1] == stop:
                continue
            i = direction.index(stop)
            headway = HEADWAY_MIN[line]
            first = (2 * i + len(line) - now_min) % headway   # minutes until the next train
            for k in range(count):
                departures.append({
                    "line": line, "towards": STOPS[direction[-1]], "in_min": round(first + k * headway),
                    "next_stops": direction[i + 1:i + 1 + next_stops],
                })
    departures.sort(key=lambda d: d["in_min"])
    return departures[:count]
