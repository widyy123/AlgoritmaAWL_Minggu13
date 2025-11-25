def schedule(requests: List[Request],
             head_position: int = 50,
             direction: str = "up",
             params: dict = None) -> List[Tuple[int,int,float,float,int]]:
    if params is None:
        params = {'max_wait': 10.0, 'zero_dist_multiplier': 1000.0, 'verbose': True}

    all_jobs = list(requests)           # semua job (dengan arrival)
    pending: List[Request] = []
    time = 0
    head = head_position
    direction = direction.lower()
    order = []

    if params.get('verbose'):
        print(f"Start: head={head}, direction={direction}, total={len(all_jobs)}")

    # helper: move newly arrived jobs to pending
    def add_arrivals():
        nonlocal pending
        arriving = [j for j in all_jobs if j.arrival <= time and j not in pending and j.completed_time is None]
        pending.extend(arriving)

    add_arrivals()

    while pending or any(j.completed_time is None for j in all_jobs):
        add_arrivals()

        if not pending:
            # nothing pending now — advance time to next arrival
            future = [j.arrival for j in all_jobs if j.arrival > time]
            if not future:
                break
            time = min(future)
            add_arrivals()
            continue

        candidates = select_in_direction(pending, head, direction)
        if not candidates:
            # if no candidates in this direction but there ARE pending in opposite direction, reverse
            if any(r for r in pending):
                direction = "down" if direction == "up" else "up"
                if params.get('verbose'):
                    print(f"Time={time}: no candidates in current dir -> reverse to {direction}")
                continue
            else:
                # should not reach here because pending non-empty handled earlier
                pass

        # compute scores and pick
        scored = [(compute_score(r, head, params), r) for r in candidates]
        scored.sort(key=lambda x: (x[0], x[1].priority, -abs(x[1].track - head), -x[1].id), reverse=True)
        chosen_score, chosen = scored[0]

        dist = abs(chosen.track - head)
        travel_time = max(1, dist)  # or dist if you want 0 -> 0
        if params.get('verbose'):
            print(f"Time={time}: chosen {chosen.id} track={chosen.track} dist={dist} score={chosen_score:.3f}")

        # advance time, move head, mark complete
        time += travel_time
        head = chosen.track
        chosen.completed_time = time
        order.append((chosen.id, chosen.track, chosen.priority, chosen.wait, chosen.completed_time))
        pending.remove(chosen)

        # update wait only for jobs that were pending (i.e., have arrived and not completed)
        for r in pending:
            r.wait += travel_time

    return order