package postgres

import (
	"time"

	"github.com/jackc/pgx/v5/pgtype"
)

// timeToTimestamp converts time.Time to pgtype.Timestamp
func timeToTimestamp(t time.Time) pgtype.Timestamp {
	return pgtype.Timestamp{
		Time:  t,
		Valid: !t.IsZero(),
	}
}

// timestampToTime converts pgtype.Timestamp to time.Time
func timestampToTime(ts pgtype.Timestamp) time.Time {
	if !ts.Valid {
		return time.Time{}
	}
	return ts.Time
}
